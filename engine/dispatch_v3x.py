"""Bot cua doi: starter cua kit, doi cac quyet dinh ve gia va phi.

v2 (bat bang --param learn=true): hoc muc gia dealer chap nhan ngay trong tuan, tu moi lan thang/thua,
roi bao muc gia co lai ky vong cao nhat. Xe it thoi gian du bi tinh them chi phi rui ro tre.

v1 (mac dinh): ba quyet dinh co dinh:

1. Bao gia: mot boi so cua list price cho moi option du an toan; xe rui ro thi tu choi.
2. Phi tai xe: mot muc co dinh cho moi gig (khong tang dan, de tai xe khong hoc cach cho).
3. Sau canh bao deadline: nang phi dung mot lan.

Chay:  python dispatch.py --level 8 --seed test-1 --param price=1.5 --param fee=1.1
Phan con lai (vong lap, ket noi lai, --final, --board) dung nguyen cua starter.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import random
import re
import sys
import zlib
from dataclasses import dataclass, fields

import spread.starter as starter
from spread.starter import DAY, HOUR
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
    # --- v2: hoc gia trong tuan ---
    learn: bool = False        # bat hoc gia; khi bat, `price` khong con dung
    level0: float = 1.33       # du doan ban dau: dealer chap nhan 50% o muc level0 x list
    slope: float = 10.0        # do doc duong cong thang (gia tang 10% thi kha nang thang giam ro)
    sd_world: float = 0.10     # do bat dinh ve muc gia cua ca tuan (thang log)
    sd_day: float = 0.10       # ... cua tung ngay (bat price war, outage)
    sd_dealer: float = 0.07    # ... cua tung dealer
    speed: float = 0.09        # option cham hon thi dealer chap nhan gia thap hon chung nay (log) moi bac
    reserve: float = 0.10      # lai toi thieu moi don, tinh theo ti le chi phi
    late_eur: float = 80.0     # chi phi ngam cua mot don tre, ngoai tien hoan (giu nguong 90%)
    max_backlog: int = 45      # so don dang cho tai xe toi da; vuot thi ngung nhan xe moi
    # --- v3: nang phi som cho gig e, va tinh rui ro theo so tai xe o gan ---
    step1_h: float = 14.0      # con chung nay gio truoc lan lay xe cuoi ma chua ai nhan thi nang phi lan 1
    step1_fee: float = 1.25    # muc phi lan 1 (x typical); 0 = tat
    step2_h: float = 7.0       # tuong tu, lan 2
    step2_fee: float = 1.5     # muc phi lan 2; 0 = tat
    # --- do the gioi: gia ngau nhien va phi ngau nhien, de co du lieu cho mo hinh ---
    explore: bool = False      # bat thi moi quyet dinh la ngau nhien co kiem soat; chi dung cho tuan tap


P = Params()
DECLINE = 4  # bao gia gap 4 lan list: khong bao gio thang, va khong mat thien cam cua dealer


def crow_km(a: tuple, b: tuple) -> float:
    """Khoang cach duong chim bay giua hai diem (vi do, kinh do), tinh bang km."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def euros(cents: float) -> int:
    """Lam tron ve euro chan, tinh bang cent."""
    return int(cents / 100 + 0.5) * 100


class Desk(starter.Desk):
    def __init__(self, world, level, now):
        super().__init__(world, level, now)
        roads = world.client.map()["roads"]  # ban do khong ton token
        self.minutes = {(r["from"], r["to"]): r["minutes"] for r in roads}
        self.km = {(r["from"], r["to"]): r["km"] for r in roads}
        places = {p["id"]: (p["lat"], p["lon"]) for p in world.client.map()["places"]}
        homes = [d["homePlaceId"] for d in world.roster()]
        self.near = {p: sum(1 for h in homes if crow_km(places[h], places[p]) <= 30) for p in places}  # tai xe song trong 30 km
        self.beliefs: dict[tuple, tuple[float, float]] = {}  # v2: du doan ve muc gia
        self.quoted: dict[str, dict[str, float]] = {}        # v2: request -> option -> boi so list da bao
        self.trust: dict[str, int] = {}                      # v2: dealer -> so don dung han (toi da 25)

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
        return self.slack_hours(request, option) >= P.min_slack_h

    def slack_hours(self, request: PriceRequest, option: DeliveryOption) -> float:
        """So gio tu luc dealer tra loi den lan lay xe cuoi cung con kip han."""
        leg = request["legs"][0]
        ends = (leg["pickup"]["placeId"], leg["delivery"]["placeId"])
        last_pickup = min(leg["pickup"]["window"]["to"], option["deadline"] - self.minutes[ends])
        return (last_pickup - request["respondBy"]) / HOUR

    # ---------- v2: hoc gia ----------
    def parts(self, request: PriceRequest) -> list[tuple]:
        """Muc gia cua mot request = tong ba phan: ca tuan, ngay hom do, dealer do."""
        return [("world",), ("day", request["arrivedAt"] // DAY), ("dealer", request["dealerId"])]

    def belief(self, part: tuple) -> tuple[float, float]:
        """Du doan hien tai ve mot phan: (gia tri, do bat dinh binh phuong)."""
        if part not in self.beliefs:
            start = {"world": (math.log(P.level0), P.sd_world ** 2), "day": (0.0, P.sd_day ** 2), "dealer": (0.0, P.sd_dealer ** 2)}
            self.beliefs[part] = start[part[0]]
        return self.beliefs[part]

    def level_of(self, request: PriceRequest, index: int) -> tuple[float, float]:
        """Log cua boi so list ma dealer chap nhan 50% so lan, cho option thu `index`, va do bat dinh."""
        beliefs = [self.belief(part) for part in self.parts(request)]
        known = math.log1p(0.01 * min(25, self.trust.get(request["dealerId"], 0))) - P.speed * index
        return known + sum(m for m, _ in beliefs), sum(v for _, v in beliefs)

    def chance(self, request: PriceRequest, index: int, multiple: float) -> float:
        """Xac suat dealer nhan muc gia `multiple` x list."""
        mean, variance = self.level_of(request, index)
        logit = P.slope * (mean - math.log(multiple)) / math.sqrt(1 + math.pi * P.slope ** 2 * variance / 8)
        return 1 / (1 + math.exp(-max(-30.0, min(30.0, logit))))

    def learn(self, request_id: str, won: str | None) -> None:
        """Cap nhat du doan sau cau tra loi cua dealer: thang thi nang muc gia, thua thi ha."""
        request, quoted = self.requests.get(request_id), self.quoted.pop(request_id, None)
        if not request or not quoted:
            return
        kinds = [o["kind"] for o in request["options"]]
        if won in quoted:
            index = kinds.index(won)
        else:  # thua: dealer da can option hap dan nhat cua minh voi doi thu
            index = max((kinds.index(k) for k in quoted), key=lambda i: self.chance(request, i, quoted[kinds[i]]))
        multiple = quoted[kinds[index]]
        mean, variance = self.level_of(request, index)
        p = 1 / (1 + math.exp(-max(-30.0, min(30.0, P.slope * (mean - math.log(multiple))))))
        weight = P.slope ** 2 * p * (1 - p)
        push = P.slope * ((1.0 if won in quoted else 0.0) - p) / (1 + weight * variance)
        shrink = weight / (1 + weight * variance)
        for part in self.parts(request):
            m, v = self.belief(part)
            self.beliefs[part] = (m + v * push, max(1e-6, v - v * v * shrink))

    def late_chance(self, slack_hours: float, drivers_near: int) -> float:
        """Kha nang don tre, theo so gio du va so tai xe song gan noi lay xe (do tren cac tuan test-1, test-2 cua minh)."""
        by_slack = 0.40 if slack_hours < 5 else 0.20 if slack_hours < 8 else 0.08 if slack_hours < 12 else 0.05
        by_supply = 3.0 if drivers_near <= 3 else 1.6 if drivers_near <= 20 else 1.3 if drivers_near <= 100 else 0.6
        return min(0.9, by_slack * by_supply)

    def waiting(self) -> int:
        """So don dang cho tai xe nhan."""
        return sum(1 for order_id in self.orders if any(g not in self.booked for g in self.gigs_of(order_id)))

    def quote_learned(self, request: PriceRequest) -> None:
        options, typical, prices = request["options"], request["referenceFeeCents"], {}
        if self.waiting() < P.max_backlog:
            for index, option in enumerate(options):
                if not self.wanted(request, option):
                    continue
                cost = typical * P.fee + self.late_chance(self.slack_hours(request, option), self.near[request["legs"][0]["pickup"]["placeId"]]) * (0.54 * option["listPriceCents"] + P.late_eur * 100)
                floor = cost * (1 + P.reserve)
                gain, multiple = max(((m / 100 * option["listPriceCents"] - floor) * self.chance(request, index, m / 100), m / 100) for m in range(100, 261))
                if gain > 0:
                    prices[option["kind"]] = euros(option["listPriceCents"] * multiple)
        if prices:
            self.quoted[request["id"]] = {kind: price / next(o["listPriceCents"] for o in options if o["kind"] == kind) for kind, price in prices.items()}
        else:
            prices = {options[0]["kind"]: options[0]["listPriceCents"] * DECLINE}
        self.outbox.append({"type": "quote", "requestId": request["id"], "prices": prices})

    def handle(self, event) -> None:
        if P.learn and self.level > 3:
            if event["kind"] == "order_won":
                self.learn(event["order"]["id"], event["order"]["option"])
            elif event["kind"] == "order_lost":
                self.learn(event["requestId"], None)
            elif event["kind"] == "delivered" and event["orderId"] in self.orders:
                order = self.orders[event["orderId"]]
                left = [leg for leg in range(len(order["legs"])) if order["deliveredAt"][leg] is None and leg != event["leg"]]
                if not left:  # xe cuoi cua don: dung han thi dealer tin them 1 bac, tre thi mat mot nua
                    count = self.trust.get(order["dealerId"], 0)
                    self.trust[order["dealerId"]] = min(25, count + 1) if event["at"] <= order["deadline"] else count // 2
        super().handle(event)

    # ---------- do the gioi ----------
    def dice(self, key: str) -> random.Random:
        """Xuc xac rieng cho tung request cua tung the gioi: chay lai van ra cung so."""
        return random.Random(zlib.crc32((self.world.id + key).encode()))

    def quote_explore(self, request: PriceRequest) -> None:
        """Bao gia ngau nhien 1.0-1.9 x list cho mot tap option ngau nhien; don hai xe thi tu choi."""
        dice, options = self.dice(request["id"]), request["options"]
        if len(request["legs"]) > 1:
            prices = {options[0]["kind"]: options[0]["listPriceCents"] * DECLINE}
        else:
            chosen = [o for o in options if dice.random() < 0.5] or [dice.choice(options)]
            prices = {o["kind"]: euros(o["listPriceCents"] * dice.uniform(1.0, 1.9)) for o in chosen}
        self.outbox.append({"type": "quote", "requestId": request["id"], "prices": prices})

    # ---------- chung ----------
    def quote(self, request: PriceRequest) -> None:
        self.requests[request["id"]] = request
        options = request["options"]
        if P.explore and self.level > 3:
            return self.quote_explore(request)
        if P.learn and self.level > 3:
            return self.quote_learned(request)
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
        if P.explore:  # mot muc phi ngau nhien, giu nguyen; chi nang mot lan sau canh bao
            multiple = P.urgent_fee if order["id"] in self.urgent else self.dice("fee" + order["id"]).choice((0.7, 0.85, 1.0, 1.15, 1.3, 1.5))
            return [{"at": self.now, "feeCents": max(1, int(typical * multiple + 0.5))}]
        if order["id"] in self.urgent:
            steps = [(self.now, P.urgent_fee)]
        else:  # mot muc phi; chi nang khi gig da e den sat han, luc ma cho them la tre
            steps = [(self.now, P.fee)]
            for hours, multiple in ((P.step1_h, P.step1_fee), (P.step2_h, P.step2_fee)) if self.level > 1 else ():
                at = order["lastPickupAt"] - int(hours * HOUR)
                if multiple > steps[-1][1]:
                    if at <= steps[-1][0]:
                        steps[-1] = (steps[-1][0], multiple)
                    else:
                        steps.append((at, multiple))
        return [{"at": at, "feeCents": max(1, int(typical * multiple + 0.5))} for at, multiple in steps]


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--param", action="append", default=[], metavar="ten=gia_tri")
    args, rest = parser.parse_known_args()
    kinds = {f.name: f.type for f in fields(Params)}
    for item in args.param:
        name, _, value = item.partition("=")
        if name not in kinds:
            sys.exit(f"Khong co tham so '{name}'. Co: {', '.join(kinds)}")
        setattr(P, name, value.lower() in ("1", "true", "yes") if isinstance(getattr(P, name), bool) else type(getattr(P, name))(float(value)))
    print(f"Params: {P}", flush=True)
    starter.Desk = Desk  # starter choi voi ban Desk cua minh
    seed = rest[rest.index("--seed") + 1] if "--seed" in rest else "noseed"
    tag = re.sub(r"[^A-Za-z0-9=.,_-]", "", ",".join(args.param)) or "base"
    play = starter.play_practice

    def play_and_save(world, level):
        """Choi xong thi luu moi thu cua tuan do vao runs/ de phan tich: diem, su kien, su that ve cac don, tai xe."""
        play(world, level)
        saved = {"seed": seed, "level": level, "params": vars(P), "worldId": world.id}
        for name, read in (("score", world.score), ("events", world.events), ("roster", world.roster), ("snapshot", world.snapshot), ("reveal", world.reveal)):
            try:
                saved[name] = read()
            except Exception as error:  # tuan xep hang khong cho reveal
                saved[name] = None
                print(f"Khong luu duoc {name}: {error}", flush=True)
        os.makedirs("runs", exist_ok=True)
        path = os.path.join("runs", f"L{level}_{seed if seed != 'noseed' else world.id}_{tag}.json.gz")
        with gzip.open(path, "wt", encoding="utf-8") as out:
            json.dump(saved, out)
        print(f"Da luu {path}", flush=True)

    starter.play_practice = play_and_save
    sys.argv = [sys.argv[0]] + rest
    starter.main()


if __name__ == "__main__":
    main()
