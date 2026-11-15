"""Team bot v1. Uses the starter kit with three decisions changed.

1. Quote a multiple of list price for each safe option and decline risky cars.
2. Keep the opening fee fixed so drivers have no reason to wait for an increase.
3. Raise the fee once after the deadline warning.

Run:  python dispatch_v1.py --level 8 --seed test-1 --param price=1.5 --param fee=1.1
The starter handles the game loop, reconnection, --final, and --board.
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
    price: float = 1.45        # quote = price x list price
    fee: float = 1.15          # opening driver fee = fee x typical fee
    urgent_fee: float = 1.6    # fee after the deadline_close warning
    min_slack_h: float = 8.0   # minimum hours from the dealer's answer to the last pickup that can arrive on time
    max_km: float = 450.0      # decline lanes longer than this
    private_pickup: bool = False  # accept pickups at private addresses
    trade_in: bool = False        # accept two-car orders
    premium: bool = False         # accept premium cars, which require experienced drivers


P = Params()
DECLINE = 4  # quote four times list price to decline without losing dealer goodwill


def euros(cents: float) -> int:
    """Round to the nearest whole euro and return cents."""
    return int(cents / 100 + 0.5) * 100


class Desk(starter.Desk):
    def __init__(self, world, level, now):
        super().__init__(world, level, now)
        roads = world.client.map()["roads"]  # the map costs no tokens
        self.minutes = {(r["from"], r["to"]): r["minutes"] for r in roads}
        self.km = {(r["from"], r["to"]): r["km"] for r in roads}

    def wanted(self, request: PriceRequest, option: DeliveryOption) -> bool:
        """Check whether there is enough time for a driver to take this option before the warning."""
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
        if self.level <= 3:  # dealers ignore the quote price. Any quote wins the first option at list price. To decline, skip quoting
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
            sys.exit(f"Unknown parameter '{name}'. Available parameters: {', '.join(kinds)}")
        setattr(P, name, value.lower() in ("1", "true", "yes") if isinstance(getattr(P, name), bool) else float(value))
    print(f"Params: {P}", flush=True)
    starter.Desk = Desk  # run the starter with our Desk
    sys.argv = [sys.argv[0]] + rest
    starter.main()


if __name__ == "__main__":
    main()
