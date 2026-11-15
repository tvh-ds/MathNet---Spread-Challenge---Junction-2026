"""Team bot. Uses the starter kit with changes to pricing and fees.

v2 (--param learn=true) learns the price dealers accept during the week from each win or loss.
It quotes the price with the highest expected profit and charges for the lateness risk of cars with little slack.

v1 (default) uses three fixed rules.

1. Quote a multiple of list price for each safe option and decline risky cars.
2. Keep the opening fee fixed so drivers have no reason to wait for an increase.
3. Raise the fee once after the deadline warning.

Run:  python dispatch_v2.py --level 8 --seed test-1 --param price=1.5 --param fee=1.1
The starter handles the game loop, reconnection, --final, and --board.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import re
import sys
from dataclasses import dataclass, fields

import spread.starter as starter
from spread.starter import DAY, HOUR
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
    # --- v2 price learning within a week ---
    learn: bool = False        # learn prices and override the fixed price
    level0: float = 1.33       # initial estimate of 50% acceptance at level0 x list price
    slope: float = 10.0        # slope of the win probability curve (a 10% price increase sharply reduces wins)
    sd_world: float = 0.10     # uncertainty in the week's price level (log scale)
    sd_day: float = 0.10       # uncertainty in the daily price level (captures price wars and outages)
    sd_dealer: float = 0.07    # uncertainty in each dealer's price level
    speed: float = 0.09        # accepted log price falls by this amount for each slower option
    reserve: float = 0.10      # minimum profit per order as a share of cost
    late_eur: float = 80.0     # cost of late delivery beyond the refund, to protect the 90% threshold
    max_backlog: int = 45      # stop taking new cars if more than this many orders await a driver


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
        self.beliefs: dict[tuple, tuple[float, float]] = {}  # v2 estimate of the price level
        self.quoted: dict[str, dict[str, float]] = {}        # v2 request -> option -> quoted multiple of list price
        self.trust: dict[str, int] = {}                      # v2 dealer -> on-time orders (up to 25)

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
        return self.slack_hours(request, option) >= P.min_slack_h

    def slack_hours(self, request: PriceRequest, option: DeliveryOption) -> float:
        """Hours from the dealer's answer to the latest pickup that can arrive on time."""
        leg = request["legs"][0]
        ends = (leg["pickup"]["placeId"], leg["delivery"]["placeId"])
        last_pickup = min(leg["pickup"]["window"]["to"], option["deadline"] - self.minutes[ends])
        return (last_pickup - request["respondBy"]) / HOUR

    # ---------- v2 price learning ----------
    def parts(self, request: PriceRequest) -> list[tuple]:
        """The request's price level is the sum of the weekly, daily, and dealer components."""
        return [("world",), ("day", request["arrivedAt"] // DAY), ("dealer", request["dealerId"])]

    def belief(self, part: tuple) -> tuple[float, float]:
        """The current estimate for one component as (value, variance)."""
        if part not in self.beliefs:
            start = {"world": (math.log(P.level0), P.sd_world ** 2), "day": (0.0, P.sd_day ** 2), "dealer": (0.0, P.sd_dealer ** 2)}
            self.beliefs[part] = start[part[0]]
        return self.beliefs[part]

    def level_of(self, request: PriceRequest, index: int) -> tuple[float, float]:
        """The log price multiple the dealer accepts half the time for option `index`, with its variance."""
        beliefs = [self.belief(part) for part in self.parts(request)]
        known = math.log1p(0.01 * min(25, self.trust.get(request["dealerId"], 0))) - P.speed * index
        return known + sum(m for m, _ in beliefs), sum(v for _, v in beliefs)

    def chance(self, request: PriceRequest, index: int, multiple: float) -> float:
        """Probability that the dealer accepts `multiple` times list price."""
        mean, variance = self.level_of(request, index)
        logit = P.slope * (mean - math.log(multiple)) / math.sqrt(1 + math.pi * P.slope ** 2 * variance / 8)
        return 1 / (1 + math.exp(-max(-30.0, min(30.0, logit))))

    def learn(self, request_id: str, won: str | None) -> None:
        """Update the price estimate after the dealer replies. A win raises it and a loss lowers it."""
        request, quoted = self.requests.get(request_id), self.quoted.pop(request_id, None)
        if not request or not quoted:
            return
        kinds = [o["kind"] for o in request["options"]]
        if won in quoted:
            index = kinds.index(won)
        else:  # on a loss, the dealer weighed our most attractive option against the competitor
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

    def late_chance(self, slack_hours: float) -> float:
        """Probability of a late order by slack hours, measured by other teams. Our own weeks will provide new estimates."""
        return 0.45 if slack_hours < 5 else 0.22 if slack_hours < 8 else 0.08 if slack_hours < 12 else 0.04

    def waiting(self) -> int:
        """Number of orders waiting for a driver."""
        return sum(1 for order_id in self.orders if any(g not in self.booked for g in self.gigs_of(order_id)))

    def quote_learned(self, request: PriceRequest) -> None:
        options, typical, prices = request["options"], request["referenceFeeCents"], {}
        if self.waiting() < P.max_backlog:
            for index, option in enumerate(options):
                if not self.wanted(request, option):
                    continue
                cost = typical * P.fee + self.late_chance(self.slack_hours(request, option)) * (0.54 * option["listPriceCents"] + P.late_eur * 100)
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
                if not left:  # last car in the order. Add one trust point if on time, or halve trust if late
                    count = self.trust.get(order["dealerId"], 0)
                    self.trust[order["dealerId"]] = min(25, count + 1) if event["at"] <= order["deadline"] else count // 2
        super().handle(event)

    # ---------- shared logic ----------
    def quote(self, request: PriceRequest) -> None:
        self.requests[request["id"]] = request
        options = request["options"]
        if P.learn and self.level > 3:
            return self.quote_learned(request)
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
        setattr(P, name, value.lower() in ("1", "true", "yes") if isinstance(getattr(P, name), bool) else type(getattr(P, name))(float(value)))
    print(f"Params: {P}", flush=True)
    starter.Desk = Desk  # run the starter with our Desk
    seed = rest[rest.index("--seed") + 1] if "--seed" in rest else "noseed"
    tag = re.sub(r"[^A-Za-z0-9=.,_-]", "", ",".join(args.param)) or "base"
    play = starter.play_practice

    def play_and_save(world, level):
        """Save the completed week's score, events, and ground truth about orders and drivers to runs/ for analysis."""
        play(world, level)
        saved = {"seed": seed, "level": level, "params": vars(P), "worldId": world.id}
        for name, read in (("score", world.score), ("events", world.events), ("roster", world.roster), ("reveal", world.reveal)):
            try:
                saved[name] = read()
            except Exception as error:  # ranking weeks cannot be revealed
                saved[name] = None
                print(f"Could not save {name}: {error}", flush=True)
        os.makedirs("runs", exist_ok=True)
        path = os.path.join("runs", f"L{level}_{seed}_{tag}.json.gz")
        with gzip.open(path, "wt", encoding="utf-8") as out:
            json.dump(saved, out)
        print(f"Saved {path}", flush=True)

    starter.play_practice = play_and_save
    sys.argv = [sys.argv[0]] + rest
    starter.main()


if __name__ == "__main__":
    main()
