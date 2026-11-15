"""Bot v1 cua doi: starter cua kit, doi dung ba quyet dinh.

1. Bao gia: mot boi so cua list price cho moi option du an toan; xe rui ro thi tu choi.
2. Phi tai xe: mot muc co dinh cho moi gig (khong tang dan, de tai xe khong hoc cach cho).
3. Sau canh bao deadline: nang phi dung mot lan.

Chay:  python dispatch.py --level 8 --seed test-1 --param price=1.5 --param fee=1.1
Phan con lai (vong lap, ket noi lai, --final, --board) dung nguyen cua starter.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, fields

import spread.starter as starter
from spread.starter import HOUR
from spread.types import DeliveryOption, FeeStep, Order, PriceRequest


@dataclass
class Params:
    price: float = 1.45        # gia bao = price x list price
    fee: float = 1.15          # phi tai xe = fee x typical fee, giu nguyen tu luc dang
    urgent_fee: float = 1.6    # phi sau canh bao deadline_close
    min_slack_h: float = 8.0   # so gio toi thieu tu luc dealer tra loi den lan lay xe cuoi cung con kip han
    max_km: float = 450.0      # tuyen dai hon thi tu choi
    private_pickup: bool = False  # co nhan xe lay o dia chi tu nhan khong
    trade_in: bool = False        # co nhan don hai xe khong
    premium: bool = False         # co nhan xe premium khong (can tai xe kinh nghiem)


P = Params()
DECLINE = 4  # bao gia gap 4 lan list: khong bao gio thang, va khong mat thien cam cua dealer


def euros(cents: float) -> int:
    """Lam tron ve euro chan, tinh bang cent."""
    return int(cents / 100 + 0.5) * 100


class Desk(starter.Desk):
    def __init__(self, world, level, now):
        super().__init__(world, level, now)
        roads = world.client.map()["roads"]  # ban do khong ton token
        self.minutes = {(r["from"], r["to"]): r["minutes"] for r in roads}
        self.km = {(r["from"], r["to"]): r["km"] for r in roads}

    def wanted(self, request: PriceRequest, option: DeliveryOption) -> bool:
        """Co nen thang xe nay voi option nay khong: du thoi gian de mot tai xe nhan truoc canh bao."""
        legs = request["legs"]
        if len(legs) > 1 and not P.trade_in:
            return False
        leg = legs[0]
        if leg["pickup"]["privateAddress"] and not P.private_pickup:
            return False
        if any(l["car"]["premium"] for l in legs) and not P.premium:
            return False
        ends = (leg["pickup"]["placeId"], leg["delivery"]["placeId"])
        if self.km[ends] > P.max_km:
            return False
        last_pickup = min(leg["pickup"]["window"]["to"], option["deadline"] - self.minutes[ends])
        return last_pickup - request["respondBy"] >= P.min_slack_h * HOUR

    def quote(self, request: PriceRequest) -> None:
        self.requests[request["id"]] = request
        options = request["options"]
        if self.level <= 3:  # dealer bo qua gia: moi quote deu thang option dau o list price, tu choi = khong quote
            if self.wanted(request, options[0]):
                super().quote(request)
            return
        prices = {o["kind"]: euros(o["listPriceCents"] * P.price) for o in options if self.wanted(request, o)}
        if not prices:
            prices = {options[0]["kind"]: options[0]["listPriceCents"] * DECLINE}
        self.outbox.append({"type": "quote", "requestId": request["id"], "prices": prices})

    def fees_for(self, order: Order, cars: int) -> list[FeeStep]:
        typical = self.requests[order["id"]]["referenceFeeCents"] * cars / len(order["legs"])
        multiple = P.urgent_fee if order["id"] in self.urgent else P.fee
        return [{"at": self.now, "feeCents": max(1, int(typical * multiple + 0.5))}]


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--param", action="append", default=[], metavar="ten=gia_tri")
    args, rest = parser.parse_known_args()
    kinds = {f.name: f.type for f in fields(Params)}
    for item in args.param:
        name, _, value = item.partition("=")
        if name not in kinds:
            sys.exit(f"Khong co tham so '{name}'. Co: {', '.join(kinds)}")
        setattr(P, name, value.lower() in ("1", "true", "yes") if isinstance(getattr(P, name), bool) else float(value))
    print(f"Params: {P}", flush=True)
    starter.Desk = Desk  # starter choi voi ban Desk cua minh
    sys.argv = [sys.argv[0]] + rest
    starter.main()


if __name__ == "__main__":
    main()
