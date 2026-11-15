"""Spread dispatcher, team MathNet1.

One idea runs through the desk: a car costs its fee plus its risk.

  drivers  For every car a model, measured on our own practice weeks (fit.py -> model.json), says how likely
           the car is to arrive on time at each fee. The gig gets the one fee where fee + risk is smallest,
           and that sum is what the car costs us.
  dealers  Every yes and no teaches the desk what this week's dealers pay (one Kalman step per answer).
           The quote is the price with the highest expected margin over the car's cost.
  minimum  The 90% delivery minimum is a price, not a rule: a late order costs almost nothing while we
           expect far fewer late orders than we allow ourselves, and a lot near that share.

world.py holds the facts of a world (roads, opening hours, where drivers live). notes_exactum.py is the
dealer-note reader of team EX-ACTUM, used unchanged under its MIT licence. Orders, gigs, the two loops and
the restart are the kit starter's.

    python dispatch.py --level 8 --seed test-1
    python dispatch.py --level 8 --seed test-1 --param on_time=0.95 --param look_h=0
    python dispatch.py --final
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
import time
import zlib
from dataclasses import dataclass, fields
from typing import Optional

import spread.starter as starter
from spread.starter import DAY, HOUR
from spread.types import DeliveryOption, FeeStep, Order, PriceRequest, StopRef

from notes_exactum import parse_note
from world import PLATES, Atlas, crow_km, first_open, last_open, open_span, with_fee, work_after, work_before

END = 9 * DAY + 22 * HOUR  # the world ends on the second Wednesday at 22:00
DECLINE = 4                # times the list price: a quote that never wins and costs no goodwill
HERE = os.path.dirname(os.path.abspath(__file__))
MULTIPLES = [m / 100 for m in range(60, 301)]  # the prices we consider, as multiples of the list price
LIVE = "--final" in sys.argv  # the live clock: keep a journal, so a restart continues as the same desk


@dataclass
class Params:
    # --- drivers: the fee of a gig ---
    fees: str = "0.7,0.85,1.0,1.15,1.3,1.5"  # the fees a gig may show, as multiples of the typical fee (the fees fit.py measured)
    urgent_fee: float = 1.6     # after the deadline warning
    urgent_more: float = 0.0    # the fee of a car still without a driver half an hour after its warning; 0 = it stays at the urgent fee
    lost_h: float = 0.0         # a car that loses its driver with fewer hours than this to its last pickup goes at the urgent fee at once (0 = never:
                                # coming back as a new gig one fee step up does as well, measured, and costs less)
    last_fee: float = 2.5       # a late car still without a driver in the world's last day and a half: left undelivered it costs twice its price
    late_fee: float = 1.0       # once its last pickup has passed without a driver a car can only arrive late: it then starts again from this fee,
                                # one step up every four working hours (0 = it stays at the urgent fee, which no longer buys anything and
                                # takes drivers from the cars that can still be on time: EUR 860 a week, measured, and more cars on time)
    look_h: float = 6.0         # a gig without a driver after this many working hours in the app goes one fee step up; 0 = never
    marks: str = "8,5"          # and one more step up each time this many working hours remain before its last pickup ("" = never)
    drift: float = 0.0          # what a gig is expected to pay beyond that, in typical fees (research knob)
    morning: bool = True        # each working morning, a gig left from an earlier day is taken out and posted again: the app tells the day's drivers of a new gig
                                # (EUR +181 a week +- 84 on 115 weeks never played before, and the worst of them at 91.6% on time instead of 90.0%)
    fresh: bool = True          # a gig that must find a driver soon (its fee goes a step up, its driver is lost, its deadline warning comes) is taken
                                # out and posted again as a new gig: the app tells the drivers nearby of a new gig, never of a new fee
    # --- the delivery minimum as a price ---
    on_time: float = 0.96       # the share of orders we want on time: the minimum of 90% with room for a bad week
    late_eur: float = 300.0     # what a late order costs beyond its refund when expected late orders reach that share
    calm_eur: float = 150.0     # the most of that price a fee is chosen against: the minimum is held by which cars we win, not by overpaying drivers
                                # (a higher fee takes a driver from another car of ours more than it adds one: 150 earned more than 300)
    grip: float = 4.0           # how steeply that price rises on the way there
    calm: float = 20.0          # orders: a week's first orders say little about its share of late ones
    ease: float = 0.0           # after a bad night the week's late share is past mending: a car then uses room only if it is riskier than
                                # that share less this much (0.02 = two points); 0 = always measured against the wanted share
    ease_top: float = 0.0       # the most that share may ease to (0.06 = six late orders in a hundred); 0 = no limit
    give_back: bool = True      # a car safer than the minimum needs gives room back: its cost falls by that room, at no more than calm_eur a late order
    start: float = 0.0          # the share of our allowance of late orders that the week is taken to have used before its first order
    doubt: float = 4.0          # how firmly we hold that this week's drivers are the model's, in outcomes
    caution: float = 0.0        # logits taken off every chance of arriving on time (research knob)
    crowd: float = 0.0          # how much of the lateness that a new car brings on the cars already waiting counts in its cost (research knob)
    stake: float = 1.0          # how much of the dealer's trust that a late car destroys counts in its cost (1 = all of it)
    # --- dealers: the price level, learned during the week ---
    level0: float = 1.33        # before any answer: a dealer buys half the time at level0 x list
    slope: float = 10.0         # how fast a yes fades as the price rises (logits per unit of log price)
    price_slope: float = 0.0    # the same, when choosing a price; 0 = the learner's slope (research knob: a flatter curve asks for more margin)
    sd_world: float = 0.10      # how far each part of the level may stray from its prior (log price)
    sd_day: float = 0.10
    sd_dealer: float = 0.05
    sd_to: float = 0.05
    sd_from: float = 0.03
    sd_here: float = 0.04       # the pickup town on one day
    sd_lane: float = 0.0        # one yard-to-site lane; 0 = lanes are not learned apart
    outage: float = 2.0         # a dealer whose competitor is down for the day buys half the time at this multiple of list; 0 = do not look for outages
    outage_slope: float = 10.6  # and how fast that yes fades as the price rises (both measured in weeks of quotes up to 3.4 x list)
    outage_prior: float = 0.2   # the chance, before any answer, that the competitor is down somewhere today: one region, one working day a week
    backup: float = 0.0         # a dealer whose competitor is down turns to a backup that costs this many times the competitor's price (HANDBOOK:
                                # about 1.3; our own answers: 1.26). The dealer's usual curve then holds, moved up by that; 0 = the fixed curve above
    gap_next: float = 16.0      # euros less that a dealer pays for the next day than for the same day (one sum on every lane, short or long)
    gap_later: float = 9.0      # and for within three days than for the next day
    trust: float = 0.01         # log price a dealer adds for each order delivered to it on time (RULES.md: 1%, up to 25)
    invest: float = 0.0         # how much of the trust that an on-time order builds counts in its price: the dealer's later orders this week
                                # sell for 1% more each (0 = an order is priced for its own margin alone)
    reserve: float = 0.1        # what one more car costs the cars that already wait (its driver is one they do not get), as a share of its own cost:
                                # every order must earn this much above its cost. Measured: 0 -> 0.1 EUR +1,160 a week on 8 of 8 weeks and
                                # more cars on time; 0.2 is past the top, 0.3 far past it
    reserve_q: float = 0.0      # the number of waiting cars at which that share holds: with fewer it is smaller, with more larger; 0 = it is constant
    reserve_tight: float = 0.0  # and how far it follows the week: in a week that uses up its room for late cars a driver is worth more
                                # (the share times that use, between a half and two, to this power; 0 = not at all)
    menu: bool = True           # quote every option the dealer accepts at one margin, so the dealer chooses its speed
    # --- two cars for one driver ---
    pairs: bool = True          # a new car shares a gig with a car that waits, when the second starts where the first ends
    pair_fee: float = 0.75      # the fee of such a gig, as a multiple of the two typical fees together
    pair_small: float = 0.9     # the same for a small gig: a driver does not come out for little money
    pair_small_eur: float = 90.0  # the two typical fees together under which a gig is small
    pair_friday: bool = False   # pair on Friday too (most drivers know only their next working day: a Friday pair rarely finds one)
    pair_km: float = 30.0       # how far the second car may start from where the first ends
    pair_max_h: float = 5.0     # the most planned driving of such a gig, in hours (the world allows 12)
    pair_wait: float = 45.0     # minutes a two-car gig may wait for a driver before its cars go alone (those that find one find it within minutes)
    pair_hold: float = 0.0      # minutes a new car may stay out of the app to wait for a new partner (two new cars find a driver far more often
                                # than a new car with one that has sat); 0 = none
    # --- what we take ---
    trade_in: bool = False      # orders with two cars
    lane_cap: int = 8           # the most of our cars that may wait for a driver on one long lane; a car beyond that is declined (0 = no limit).
                                # It changed 3 of 60 weeks: the week of the Joensuu batch by EUR +1,464 (90.0% -> 91.4% on time), two others by -173 and -120
    lane_km: float = 200.0      # from this many kilometres on a lane is long: a driver gives it a day, and a thin town has few drivers to give one
    min_room_h: float = 1.0     # hours a car needs between the dealer's answer and its last pickup
    notes: bool = True          # read the dealer's note
    # --- measuring the world ---
    explore: bool = False       # random prices and random fees: practice weeks only
    explore_lo: float = 1.0     # the random prices of an explore week, as multiples of list: from
    explore_hi: float = 1.9     # to
    try_fees: bool = False      # our own quotes, but each gig opens at a random fee of the grid: weeks to refit the model on
    tag: str = ""               # a label for the saved week; decides nothing


P = Params()


def euros(cents: float) -> int:
    """Cents rounded to whole euros."""
    return int(cents / 100 + 0.5) * 100


ARRIVALS = (0.22, 0.20, 0.20, 0.21, 0.17)  # the share of a week's requests that comes on each working day (measured)
DEALER_WEEK = 26                           # the requests of one dealer in a week, on average: a few send hundreds, most a handful


def arrived(at: int) -> float:
    """The share of the week's requests that has come by this minute: on working days, evenly from 8:30 to 18:00."""
    day = at // DAY
    return 1.0 if day > 4 else sum(ARRIVALS[:day]) + ARRIVALS[day] * min(1.0, max(0.0, (at % DAY - 510) / 570))


def chance_of(logit: float) -> float:
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, logit))))


def load_model() -> dict:
    """The numbers fit.py measured on our saved weeks."""
    with open(os.path.join(HERE, "model.json"), encoding="utf-8") as f:
        return json.load(f)


def measured(model: dict) -> None:
    """What fit.py measured about dealers becomes the defaults; a --param on the command line still wins."""
    market = model.get("market")
    if not market:
        return
    P.slope, P.level0, P.trust, (P.gap_next, P.gap_later) = market["slope"], math.exp(market["level"]), market["trust"], market["gaps"]
    for name, value in model.get("learner", {}).items():  # how fast each part of the level may move: chosen by the learner's score on saved weeks
        setattr(P, name, value)


def spans(hours: Optional[dict], since: int, until: int) -> list[tuple[int, int]]:
    """The parts of [since, until] in which a site is open."""
    out, day = [], since // DAY
    while day * DAY <= until:
        span = open_span(hours, day)
        if span and min(until, span[1]) > max(since, span[0]):
            out.append((max(since, span[0]), min(until, span[1])))
        day += 1
    return out


class Desk(starter.Desk):
    def __init__(self, world, level, now):
        super().__init__(world, level, now)
        self.atlas = Atlas(world.client.map(), world.roster())
        self.model = load_model()
        self.weights: dict[str, float] = self.model["on_time"]
        self.grid = sorted(float(x) for x in P.fees.split(","))
        self.facts: dict[str, dict] = {}                     # request -> what its note says
        self.beliefs: dict[tuple, tuple[float, float]] = {}  # part of the price level -> mean and variance
        self.quoted: dict[str, dict[str, float]] = {}        # open request -> option -> the multiple of list we quoted
        self.trust: dict[str, int] = {}                      # dealer -> orders delivered on time (late halves it)
        self.down: dict[int, dict[str, float]] = {}          # day -> town -> the chance that the competitor is down today in that town's region
        self.steps: dict[str, list[tuple[int, float]]] = {}  # order -> the fee steps of its last gig, as multiples of the typical fee
        self.opened: dict[str, float] = {}                   # order -> the fee multiple its first gig opened at (saved with a practice week, for fit.py)
        self.trace: list[tuple] = []                         # (minute, late price in euros, world shift, orders waiting, orders won, late orders expected), every two hours
        self.forecast: dict[str, float] = {}                 # order -> the model's logit when its first gig was posted
        self.ended: dict[str, bool] = {}                     # delivered order -> on time?
        self.won = 0
        self.world_shift = 0.0                               # how much easier (+) this week's drivers are than the model's
        self.late_price = 0.0                                # cents that one more late order costs beyond its refund
        self.late_share = 0.0                                # the share of this week's orders that we expect late, as things stand
        self.crowding = 0.0                                  # how much later the cars that wait become, in late cars, when the queue grows by one log unit
        self.seen_at = -1
        self.journal = os.path.join(HERE, "journal", world.id + ".jsonl") if LIVE else None  # what a restart cannot read back from the world
        self.partner: dict[str, str] = {}                    # order -> the order that shares its gig
        self.tried: set[str] = set()                         # orders whose two-car gig found no driver: they go alone from then on
        self.held: dict[str, int] = {}                       # order kept out of the app for a partner -> until which minute
        self.timers: list[tuple[int, str, str]] = []         # (minute, "split" a gig or "post" an order, its id)
        self.refused: list = []                              # the actions of the last send that the world refused
        self.dropped: set[str] = set()                       # orders that lost their driver since their gig was last posted
        self.last_call = now >= END - 36 * HOUR              # the last day and a half of the world: any car left needs a driver at any fee
        self.given_up: set[str] = set()                      # orders that can only arrive late and have started again from the late fee
        self.unlucky: set[str] = set()                       # orders that ever lost a driver: what became of them says nothing of how the week's drivers take a new gig
        self.rescued: dict[str, int] = {}                    # order -> how often it was found without any gig and posted again
        self.rescued_at = -1
        self.refusals: dict[str, int] = {}                   # kind of action -> how many the world refused this week
        if P.morning:
            self.timers += [(day * DAY + 8 * HOUR + 5, "morning", "") for day in range(now // DAY + 1, END // DAY + 1) if day % 7 < 5]
        self.timers.append((max(now + 1, END - 36 * HOUR), "last call", ""))

    # ------------------------------------------------------------------ the car
    def note(self, request: PriceRequest) -> dict:
        if request["id"] not in self.facts:
            text = request["note"]["text"] if P.notes and request.get("note") else None
            self.facts[request["id"]] = parse_note(text, request["arrivedAt"])
        return self.facts[request["id"]]

    def ready(self, request: PriceRequest) -> int:
        """The minute from which the first car can be collected, by the note."""
        facts = self.note(request)
        return max(facts["ready_at"] or 0, facts["release_at"] or 0)

    def last_pickup(self, request: PriceRequest, deadline: int) -> Optional[int]:
        """The last minute to collect the car and still arrive on time, by the real hours and the note's deadline."""
        facts = self.note(request)
        if facts["deadline_at"] and facts["deadline_at"] > request["arrivedAt"]:
            deadline = min(deadline, facts["deadline_at"])
        return self.atlas.last_pickup(request["legs"][0], deadline, facts["pickup_close"], facts["delivery_close"], PLATES if facts["plates"] else 0)

    def car(self, request: PriceRequest, deadline: int, at: int) -> Optional[dict]:
        """The signs of how easily the car finds a driver in time, seen at minute `at`; None when no driver can make it."""
        last, ready = self.last_pickup(request, deadline), self.ready(request)
        if last is None or last < max(at, ready) + P.min_room_h * HOUR:
            return None
        return self.atlas.signs(request, last, at, ready)

    # ------------------------------------------------------------------ drivers: the chance of arriving on time
    def waits(self, order_id: str) -> bool:
        """True for an order that the drivers can see and have not taken."""
        gigs = self.gigs_of(order_id)
        return bool(gigs) and any(gig not in self.booked for gig in gigs)

    def queue(self, but: Optional[str] = None) -> tuple[int, float]:
        """The orders that wait for a driver now, but for one: how many, and the sum of the fee multiples they show."""
        waiting = [order_id for order_id in self.orders if order_id != but and self.waits(order_id)]
        return len(waiting), sum(self.shown(order_id) for order_id in waiting)

    def shown(self, order_id: str) -> float:
        """The fee multiple that the order's gig shows in the app now."""
        steps = self.steps.get(order_id) or [(0, 1.0)]
        return next((multiple for at, multiple in reversed(steps) if at <= self.now), steps[0][1])

    def logit(self, car: dict, multiple: float, queue: tuple[int, float]) -> float:
        """The model's log odds that the car arrives on time when its gig opens at this fee, next to the gigs that already wait."""
        signs = with_fee(dict(car, backlog=math.log1p(queue[0])), multiple)
        return sum(weight * signs[name] for name, weight in self.weights.items()) - P.caution

    def on_time(self, car: dict, multiple: float, queue: tuple[int, float]) -> float:
        return chance_of(self.logit(car, multiple, queue) + self.world_shift)

    def driver_in_time(self, on_time: float) -> float:
        """The chance that a driver books the gig before its deadline warning, read off the chance of arriving on time:
        a car with a driver in time is late now and then, a car without one is on time now and then (both measured)."""
        with_driver, without = 1 - self.model["booked_late"], 1 - self.model["unbooked_late"]
        return max(0.0, min(1.0, (on_time - without) / (with_driver - without)))

    def paid(self, multiple: float, on_time: float, car: Optional[dict] = None, queue: tuple[int, float] = (0, 0.0)) -> float:
        """What a gig that opens at this fee is expected to pay in the end, in typical fees: a gig that waits goes up fee steps, so a low
        opening fee pays more than itself. Measured on our own weeks; without that measurement: its own fee, or the urgent one when
        no driver came before the warning."""
        weights = self.model.get("paid")
        if weights and car is not None:
            signs = with_fee(dict(car, backlog=math.log1p(queue[0])), multiple)
            return max(multiple, min(P.urgent_fee, sum(weight * signs[name] for name, weight in weights.items()))) + P.drift
        booked = self.driver_in_time(on_time)
        return multiple * booked + max(multiple, P.urgent_fee) * (1 - booked) + P.drift

    def fee(self, car: dict, typical: float, late_cost: float, queue: tuple[int, float], floor: float = 0.0) -> tuple[float, float]:
        """The fee multiple at which what we expect to pay in fees plus the risk of a late car is smallest, and the chance that the car is late at it."""
        def total(multiple: float) -> float:
            on_time = self.on_time(car, multiple, queue)
            return self.paid(multiple, on_time, car, queue) * typical + (1 - on_time) * late_cost
        multiple = min([m for m in self.grid if m >= floor] or [floor], key=total)
        return multiple, 1 - self.on_time(car, multiple, queue)

    def look(self) -> None:
        """Once a turn: what this week's own orders say about its drivers, against what the model said when each was posted,
        and from the late orders we now expect, the price of one more."""
        if self.seen_at == self.now:
            return
        self.seen_at, queue, booked_late = self.now, self.queue(), self.model["booked_late"]
        seen, waiting, late = [], [], 0.0  # (forecast, outcome) of each order; the logits now of those that wait; late orders so far
        for order_id in self.orders:
            if order_id in self.ended:
                outcome = float(self.ended[order_id])
            elif self.overdue(order_id):
                outcome = 0.0
            elif self.waits(order_id):
                order, shown = self.orders[order_id], self.shown(order_id)
                car = self.car(self.requests[order_id], order["deadline"], self.now)
                waiting.append(-30.0 if car is None else self.logit(car, shown, (queue[0] - 1, queue[1] - shown)))
                outcome = chance_of(waiting[-1])
            else:
                outcome = 1 - booked_late
            if order_id in self.forecast and order_id not in self.unlucky:
                seen.append((self.forecast[order_id], outcome))
            late += 1 - outcome
        shift = 0.0
        for _ in range(4):  # Newton's method on one number, from a prior that the world is the model's
            chances = [chance_of(forecast + shift) for forecast, _ in seen]
            shift += (sum(outcome - c for (_, outcome), c in zip(seen, chances)) - P.doubt * shift) / (sum(c * (1 - c) for c in chances) + P.doubt)
        self.world_shift = max(-1.5, min(1.5, shift))
        late += sum(chance_of(now) - chance_of(now + self.world_shift) for now in waiting)  # the orders that wait, as this week's world treats them
        chances = [chance_of(now + self.world_shift) for now in waiting]
        self.crowding = -self.weights.get("backlog", 0.0) * sum(c * (1 - c) for c in chances)
        used = (late / (1 - P.on_time) + P.start * P.calm) / (P.calm + self.won)
        self.late_share = used * (1 - P.on_time)
        self.late_price = P.late_eur * 100 * min(2.0, max(0.0, used)) ** P.grip
        if not self.trace or self.now - self.trace[-1][0] >= 2 * HOUR:
            self.trace.append((self.now, round(self.late_price / 100), round(self.world_shift, 2), queue[0], self.won, round(late, 1)))

    def overdue(self, order_id: str) -> bool:
        """True for an undelivered order whose deadline has passed, or whose last pickup has passed with no driver."""
        order = self.orders[order_id]
        return self.now > order["deadline"] or (self.now > order["lastPickupAt"] and self.waits(order_id))

    def cost(self, request: PriceRequest, option: DeliveryOption) -> Optional[int]:
        """What we expect to pay, in cents, to move the car by this option's deadline: its fee, the refund of a late car,
        and its use of the room under the delivery minimum (a safe car gives room back)."""
        car = self.car(request, option["deadline"], request["respondBy"])
        if car is None:
            return None
        self.look()
        typical, refund = request["referenceFeeCents"], self.model["refund"] * option["listPriceCents"] + self.trust_at_stake(request, option["listPriceCents"])
        multiple, late = self.fee(car, typical, refund + min(self.late_price, P.calm_eur * 100), self.queue())
        allowed = max(1 - P.on_time, self.late_share - P.ease) if P.ease else 1 - P.on_time
        allowed = min(allowed, P.ease_top) if P.ease_top else allowed
        room = late - allowed  # the room under the delivery minimum that this car uses; a safe car gives some back
        risk = late * refund + room * (self.late_price if room > 0 or not P.give_back else min(self.late_price, P.calm_eur * 100))
        risk = risk if P.give_back else max(0.0, risk)
        others = P.crowd * self.crowding / (1 + self.queue()[0]) * (refund + self.late_price)  # one more car in the queue: every car that waits is a little likelier late
        return int(typical * self.paid(multiple, 1 - late, car, self.queue()) + risk + others)

    def trust_at_stake(self, request: PriceRequest, list_price: int) -> float:
        """What a late car costs beyond its refund, in cents: the dealer's count of on-time orders halves, and until it has grown back
        every order of that dealer sells for 1% less a point. From a count of n that is n * n / 8 of the dealer's orders at 1% each."""
        ours = [order for order in self.orders.values() if order["dealerId"] == request["dealerId"]]
        count = min(25, self.trust.get(request["dealerId"], 0) + sum(order["id"] not in self.ended for order in ours))  # when this car arrives: the cars on their way will have counted
        price = sum(order["priceCents"] for order in ours) / len(ours) if ours else list_price * math.exp(self.level_of(request)[0])
        return P.stake * P.trust * count ** 2 / 8 * price

    def trust_built(self, request: PriceRequest, option: DeliveryOption) -> float:
        """What an order on time adds to the dealer's later orders this week, in cents: each sells for 1% more, until the dealer's count
        is 25. Counted over the orders that the dealer is likely to give us after this one has arrived."""
        if not P.invest:
            return 0.0
        dealer = request["dealerId"]
        asked = sum(other["dealerId"] == dealer for other in self.requests.values())
        ours = [order for order in self.orders.values() if order["dealerId"] == dealer]
        room = 25 - self.trust.get(dealer, 0) - sum(order["id"] not in self.ended for order in ours)
        week = (asked + 3) / (arrived(self.now) + 3 / DEALER_WEEK)  # the dealer's requests this week, as far as those so far can tell
        later = week * (1 - arrived(option["deadline"])) * (len(ours) + 2) / (asked + 4)  # the orders it gives us after this one has arrived
        price = sum(order["priceCents"] for order in ours) / len(ours) if ours else option["listPriceCents"] * math.exp(self.level_of(request)[0])
        return P.invest * P.trust * price * max(0.0, min(later, room))

    def fees_for(self, order: Order, cars: int) -> list[FeeStep]:
        """One fee while a gig waits. It goes up one step when the gig has sat for hours and once more on its last day:
        few changes, so drivers do not learn to wait for them. After the deadline warning: the urgent fee."""
        request = self.requests[order["id"]]
        typical = request["referenceFeeCents"] * cars / len(order["legs"])
        if P.explore:
            multiple = P.urgent_fee if order["id"] in self.urgent else self.dice("fee" + order["id"]).choice((0.7, 0.85, 1.0, 1.15, 1.3, 1.5))
            return [{"at": self.now, "feeCents": max(1, int(typical * multiple + 0.5))}]
        left = order["lastPickupAt"] - self.now if order["id"] in self.dropped else END  # minutes to the last pickup of a car whose driver gave it back
        self.dropped.discard(order["id"])
        if self.last_call and self.now > order["lastPickupAt"]:
            steps = [(self.now, max(P.last_fee, self.shown(order["id"]) if order["id"] in self.steps else 0.0))]
        elif P.late_fee and self.now > order["lastPickupAt"]:  # late whatever we pay: what counts now is a driver within the day, not within the hour
            steps = [(self.now, max(P.late_fee, self.shown(order["id"])) if order["id"] in self.given_up else P.late_fee)]
            self.given_up.add(order["id"])
            for hours in (4, 8, 12):
                higher = [m for m in self.grid if m > steps[-1][1]]
                steps += [(work_after(self.now, hours * HOUR), higher[0])] if higher else []
        elif order["id"] in self.urgent or left < P.lost_h * HOUR:
            steps = [(self.now, max(P.urgent_fee, self.shown(order["id"]) if order["id"] in self.steps else 0.0))]
            if order["id"] in self.urgent and steps[0][1] < P.urgent_more:  # three hours are left at the warning: a driver who comes after the first of them comes too late
                steps.append((self.now + 30, P.urgent_more))
        else:
            self.look()
            car, queue = self.car(request, order["deadline"], self.now), self.queue(but=order["id"])
            floor = self.shown(order["id"]) if order["id"] in self.steps else 0.0  # a gig posted again never pays less than it did
            if left < DAY:  # its driver gave it back with a day or less left: one step more
                floor = next((m for m in self.grid if m > floor), floor)
            if car is None:  # the car can only arrive late now: enough for the drivers who saw it at less
                multiple = max(floor, self.grid[min(2, len(self.grid) - 1)])
            else:
                late_cost = self.model["refund"] * self.list_price(order) + self.trust_at_stake(request, self.list_price(order)) + min(self.late_price, P.calm_eur * 100)
                multiple, _ = self.fee(car, typical, late_cost, queue, floor)
                if P.try_fees and not floor:
                    multiple = self.dice("fee" + order["id"]).choice(self.grid)
                if order["id"] not in self.forecast:
                    self.forecast[order["id"]] = self.logit(car, multiple, queue)
                    self.remember({"forecast": order["id"], "logit": self.forecast[order["id"]]})
            steps = [(self.now, multiple)]
            last = min(order["lastPickupAt"], self.last_pickup(request, order["deadline"]) or order["lastPickupAt"])
            marks = [work_after(self.now, int(P.look_h * HOUR))] if P.look_h else []
            marks += [work_before(last, int(float(hours) * HOUR)) for hours in P.marks.split(",") if hours]
            marks = sorted({mark for mark in marks if self.now < mark < last - 3 * HOUR})  # working hours: a weekend in the app is no sign that the fee is too low
            for mark in marks if self.level > 1 else ():  # level 1 takes one fee only
                higher = [m for m in self.grid if m > steps[-1][1]]
                if higher:
                    steps.append((mark, higher[0]))
        self.steps[order["id"]] = steps
        self.opened.setdefault(order["id"], steps[0][1])
        if P.fresh:
            self.timers = [timer for timer in self.timers if timer[1:] != ("renew", order["id"])] + [(at, "renew", order["id"]) for at, _ in steps[1:]]
            if (P.late_fee or self.now >= END - 3 * DAY) and self.now <= order["lastPickupAt"]:
                self.timers.append((order["lastPickupAt"] + 1, "renew", order["id"]))  # the minute from which it can only be late
        return [{"at": at, "feeCents": max(1, int(typical * multiple + 0.5))} for at, multiple in steps]

    def list_price(self, order: Order) -> int:
        options = self.requests[order["id"]]["options"]
        return next((o["listPriceCents"] for o in options if o["kind"] == order["option"]), options[0]["listPriceCents"])

    # ------------------------------------------------------------------ dealers: the price level
    def parts(self, request: PriceRequest) -> list[tuple]:
        """The parts of the price level that a request touches: the week, the day, the dealer, where the car goes and comes from."""
        leg = request["legs"][0]
        day = request["arrivedAt"] // DAY
        parts = [("world",), ("day", day), ("dealer", request["dealerId"]), ("to", leg["delivery"]["placeId"]), ("from", leg["pickup"]["placeId"]),
                 ("here", leg["pickup"]["placeId"], day)]  # the yard's town today: where the competitor is down for a day, every price wins
        return parts + [("lane", leg["pickup"]["placeId"], leg["delivery"]["placeId"])] if P.sd_lane else parts

    def belief(self, part: tuple) -> tuple[float, float]:
        if part in self.beliefs:
            return self.beliefs[part]
        if part[0] == "world":
            return math.log(P.level0), P.sd_world ** 2
        prior = self.model.get("places", {}).get(part[0], {}).get(part[1], 0.0) if part[0] in ("to", "from") else 0.0
        return prior, getattr(P, "sd_" + part[0]) ** 2

    def level_of(self, request: PriceRequest) -> tuple[float, float]:
        """Mean and variance of the log multiple of list at which the dealer buys the request's fastest option half the time."""
        beliefs = [self.belief(part) for part in self.parts(request)]
        return P.trust * min(25, self.trust.get(request["dealerId"], 0)) + sum(m for m, _ in beliefs), sum(v for _, v in beliefs)

    def asked(self, request: PriceRequest, index: int, multiple: float) -> float:
        """A price for option `index`, as the dealer weighs it: the log multiple of the fastest option's list price that it comes to
        once the euros are added that the dealer gives up for each step of waiting. That sum is the same on a short lane and a long one."""
        options = request["options"]
        gap = sum(P.gap_next if option["kind"] == "same_day" else P.gap_later for option in options[:index])
        return math.log((multiple * options[index]["listPriceCents"] + gap * 100) / options[0]["listPriceCents"])

    def chance(self, request: PriceRequest, index: int, multiple: float, slope: float = 0.0) -> float:
        """The chance that the dealer buys this option at `multiple` x its list price."""
        mean, variance = self.level_of(request)
        slope = slope or P.slope
        return chance_of(slope * (mean - self.asked(request, index, multiple)) / math.sqrt(1 + math.pi * slope ** 2 * variance / 8))

    def outages(self, day: int) -> dict[str, float]:
        """For each town, the chance that the competitor is down today in its region (the town and the places within 80 km).
        Before the day's first answer every town is as likely, and less so once an earlier day of the week has shown the week's outage."""
        if day not in self.down:
            found = max((sum(towns.values()) for earlier, towns in self.down.items() if earlier < day), default=0.0)
            self.down[day] = {town: P.outage_prior * (1 - found) / len(self.atlas.reach) for town in self.atlas.reach}
        return self.down[day]

    def down_chance(self, request: PriceRequest) -> float:
        """The chance that the competitor is down at the car's yard as the request comes in: then the dealer has only its own valuation to weigh us against."""
        at, yard = request["arrivedAt"], request["legs"][0]["pickup"]["placeId"]
        if not P.outage or at // DAY % 7 > 4 or not 8 * HOUR <= at % DAY < 18 * HOUR:  # an outage lasts a working day, 08:00 to 18:00
            return 0.0
        return sum(chance for town, chance in self.outages(at // DAY).items() if yard in self.atlas.reach[town])

    def alone(self, request: PriceRequest, index: int, multiple: float) -> float:
        """The chance of a yes while the dealer's competitor is down: the dealer weighs our price against its backup."""
        if P.backup:
            mean, variance = self.level_of(request)
            ahead = mean + math.log(P.backup) - self.asked(request, index, multiple)
            return chance_of(P.slope * ahead / math.sqrt(1 + math.pi * P.slope ** 2 * variance / 8))
        return chance_of(P.outage_slope * (math.log(P.outage or 1.0) - self.asked(request, index, multiple)))

    def learn(self, request_id: str, won: Optional[str]) -> None:
        """The dealer's answer moves every part of the level it touched: up after a yes, down after a no."""
        request, quoted = self.requests.get(request_id), self.quoted.pop(request_id, None)
        if not request or not quoted:
            return
        kinds = [o["kind"] for o in request["options"]]
        if won in quoted:
            index = kinds.index(won)
        else:  # a no: the dealer weighed our best offer in its eyes against the competitor
            index = max((kinds.index(k) for k in quoted), key=lambda i: self.chance(request, i, quoted[kinds[i]]))
        mean, variance = self.level_of(request)
        p = chance_of(P.slope * (mean - self.asked(request, index, quoted[kinds[index]])))
        if self.down_chance(request) > 0:  # an answer first says where the competitor is down today; only where it is up does it speak of the price level
            yes, yard = won in quoted, request["legs"][0]["pickup"]["placeId"]
            usual, alone = self.chance(request, index, quoted[kinds[index]]), self.alone(request, index, quoted[kinds[index]])
            here, elsewhere = (alone if yes else 1 - alone), (usual if yes else 1 - usual)
            towns = self.outages(request["arrivedAt"] // DAY)
            weighed = {town: chance * (here if yard in self.atlas.reach[town] else elsewhere) for town, chance in towns.items()}
            total = max(1e-12, sum(weighed.values()) + (1 - sum(towns.values())) * elsewhere)
            self.down[request["arrivedAt"] // DAY] = {town: min(0.98, w / total) for town, w in weighed.items()}
            if self.down_chance(request) > 0.5:
                return
        weight = P.slope ** 2 * p * (1 - p)
        push = P.slope * ((1.0 if won in quoted else 0.0) - p) / (1 + weight * variance)
        shrink = weight / (1 + weight * variance)
        for part in self.parts(request):
            m, v = self.belief(part)
            self.beliefs[part] = (m + v * push, max(1e-6, v - v * v * shrink))

    def lane_full(self, request: PriceRequest) -> bool:
        """True when as many of our cars as we allow already wait for a driver on this car's lane, and the lane is long.
        A dealer's batch for one far town needs a driver a car: 18 cars from Joensuu to Oulu, sold at a good price in one morning,
        found 1 driver in time, and that week ended at 90.0% on time. On short lanes a batch is no trouble (measured)."""
        lane = (request["legs"][0]["pickup"]["placeId"], request["legs"][0]["delivery"]["placeId"])
        if not P.lane_cap or self.atlas.km[lane] < P.lane_km:
            return False
        legs = (self.requests[order_id]["legs"][0] for order_id in self.orders if self.waits(order_id))
        return sum((leg["pickup"]["placeId"], leg["delivery"]["placeId"]) == lane for leg in legs) >= P.lane_cap

    def quote(self, request: PriceRequest) -> None:
        self.requests[request["id"]] = request
        options = request["options"]
        if P.explore and self.level > 3:
            return self.quote_explore(request)
        if self.level <= 3:  # dealers ignore the price there: every quote wins the first option at list, so declining is not quoting
            if len(request["legs"]) == 1 and self.car(request, options[0]["deadline"], request["respondBy"]) is not None:
                super().quote(request)
            return
        floors, offers = {}, {}  # per option: what it must earn, and its best expected gain with the multiple that gives it
        taken = (len(request["legs"]) == 1 or P.trade_in) and not self.lane_full(request)
        for index, option in enumerate(options if taken else []):
            cost = self.cost(request, option)
            if cost is not None:
                crowd = self.queue()[0] / P.reserve_q if P.reserve_q else 1.0
                crowd *= min(2.0, max(0.5, self.late_share / (1 - P.on_time))) ** P.reserve_tight
                floors[option["kind"]] = floor = cost * (1 + P.reserve * crowd) - self.trust_built(request, option)
                down = self.down_chance(request)  # with the competitor down, the dealer buys at far higher prices
                offers[option["kind"]] = max(((m * option["listPriceCents"] - floor) * ((1 - down) * self.chance(request, index, m, P.price_slope) + down * self.alone(request, index, m)), m)
                                             for m in MULTIPLES)
        best = max(offers, key=offers.get, default=None)
        if best is None or offers[best][0] <= 0:
            prices = {options[0]["kind"]: options[0]["listPriceCents"] * DECLINE}
        else:
            lists = {o["kind"]: o["listPriceCents"] for o in options}
            margin = offers[best][1] * lists[best] - floors[best]
            prices = {kind: euros(floor + margin) for kind, floor in floors.items()} if P.menu else {best: euros(offers[best][1] * lists[best])}
            self.quoted[request["id"]] = {kind: price / lists[kind] for kind, price in prices.items()}
            self.remember({"quote": request["id"], "multiples": self.quoted[request["id"]]})
        self.outbox.append({"type": "quote", "requestId": request["id"], "prices": prices})

    # ------------------------------------------------------------------ the gig
    def post(self, order: Order, legs: list[int], retry: starter.Retry = starter.Retry()) -> None:
        request = self.requests[order["id"]]
        facts = self.note(request)
        audience = {"experienced": any(leg["car"]["premium"] for leg in order["legs"]), "manualLicence": retry.manual_licence or facts["manual"]}
        stops = starter.without_windows(self.stops(order, legs, retry), self.now)
        self.outbox.append({"type": "post", "stops": stops, "audience": audience, "schedule": self.fees_for(order, len(legs))})
        if len(legs) == 1:
            return
        self.send()  # a trade-in over the 12-hour limit for a gig with two cars goes as one gig per car
        if not self.gigs_of(order["id"]):
            for leg in legs:
                self.post(order, [leg], retry)

    def stops(self, order: Order, legs: list[int], retry: starter.Retry) -> list[StopRef]:
        """A pickup and a delivery for each car. A stop gets a window of its own only where the note or a failed visit narrows the order's."""
        request, stops = self.requests[order["id"]], []
        for leg in legs:
            facts = self.note(request) if leg == 0 else parse_note(None, 0)  # a note speaks of the first car
            first: StopRef = {"orderId": order["id"], "leg": leg, "kind": "pickup", "withPlates": retry.plates or facts["plates"],
                              "withCharging": self.atlas.needs_charging(order["legs"][leg])}
            second: StopRef = {"orderId": order["id"], "leg": leg, "kind": "delivery"}
            for stop, window in zip((first, second), self.windows(order, leg, facts, retry.pickup_from)):
                if window:
                    stop["window"] = window
            stops += [first, second]
        return stops

    def windows(self, order: Order, leg: int, facts: dict, pickup_from: int) -> tuple[Optional[dict], Optional[dict]]:
        """The windows a gig's stops need so that the driver meets the car ready and both sites really open.
        A stop has one window and real hours repeat daily, so a yard with shorter real hours gets one day's chance:
        when it passes unbooked the gig expires and the next post takes the next day."""
        pickup, delivery = order["legs"][leg]["pickup"], order["legs"][leg]["delivery"]
        deadline = min(order["deadline"], facts["deadline_at"]) if facts["deadline_at"] and facts["deadline_at"] > self.now else order["deadline"]
        yard = Atlas.narrowed(pickup["hours"], facts["pickup_open"], facts["pickup_close"])
        site = Atlas.narrowed(delivery["hours"], None, facts["delivery_close"])
        arrive, stated = last_open(site, deadline), last_open(delivery["hours"], order["deadline"])
        second = None
        if arrive is not None and stated is not None and arrive < stated and not delivery["privateAddress"] and arrive > self.now:
            second = {"from": min(delivery["window"]["from"], arrive), "to": arrive}  # the note ends the delivery before the order's window does
        start = max(self.now, pickup["window"]["from"], pickup_from, facts["ready_at"] or 0, facts["release_at"] or 0)
        last = None if arrive is None else min(arrive - self.atlas.drive(order["legs"][leg]) - (PLATES if facts["plates"] else 0), pickup["window"]["to"])
        chances = spans(yard, start, last) if last is not None else []
        if not chances:  # the car can only arrive late: collect it at the first real chance, deliver without a window
            second, chances = None, spans(yard, start, END)
        if pickup["privateAddress"] or not chances:
            return None, second
        if yard != pickup["hours"]:  # shorter real hours: one day's chance, of a useful length
            a, b = next((span for span in chances if span[1] - span[0] >= HOUR), max(chances, key=lambda span: span[1] - span[0]))
            return {"from": a, "to": b}, second
        if start > max(self.now, pickup["window"]["from"]):  # only the ready time moved
            return {"from": start, "to": max(start, pickup["window"]["to"])}, second
        return None, second

    def repost(self, gig_id: str) -> None:
        """A gig whose window ended without a driver: post its cars again, with the windows that hold now."""
        action = self.posts.get(gig_id)
        if action is None or not any(self.leg_gigs.get(s["orderId"], {}).get(s["leg"]) == gig_id for s in action["stops"]):
            return
        if len({stop["orderId"] for stop in action["stops"]}) > 1:  # a two-car gig: its cars go alone
            return self.apart(self.owners(gig_id))
        for stop in action["stops"]:
            self.leg_gigs.get(stop["orderId"], {}).pop(stop["leg"], None)
        order = self.orders.get(action["stops"][0]["orderId"])
        legs = [] if order is None else [s["leg"] for s in action["stops"] if s["kind"] == "pickup" and order["deliveredAt"][s["leg"]] is None]
        if legs:
            self.post(order, legs, starter.Retry(manual_licence=action["audience"]["manualLicence"], plates=any(s.get("withPlates") for s in action["stops"])))

    # ------------------------------------------------------------------ two cars for one driver
    def win(self, order: Order) -> None:
        if order["id"] in self.requests and order["id"] not in self.orders:
            self.orders[order["id"]] = order
            if not (P.pairs and self.level > 2 and self.plain(order) and self.pair(order)):
                self.post(order, starter.undelivered(order))

    def plain(self, order: Order) -> bool:
        """A car any driver may take at any open hour: one car, nothing in its note, no private end, not premium, no charging stop."""
        if len(order["legs"]) != 1 or order["id"] in self.urgent or order["id"] in self.tried or order["id"] in self.partner:
            return False
        leg, facts = order["legs"][0], self.note(self.requests[order["id"]])
        special = leg["car"]["premium"] or leg["pickup"]["privateAddress"] or leg["delivery"]["privateAddress"] or self.atlas.needs_charging(leg)
        return not special and not any(facts[key] for key in facts if key != "trace")

    def chain(self, x: Order, y: Order) -> Optional[int]:
        """Minutes of planned driving when one driver moves x and then y; None when y starts too far from where x ends, the drive is too long,
        or y cannot be collected in time after x. (A gig whose stops cannot all be reached in their windows loses its windows: its cars arrive days late.)"""
        first, second = x["legs"][0], y["legs"][0]
        ends = (first["delivery"]["placeId"], second["pickup"]["placeId"])
        if crow_km(self.atlas.spot[ends[0]], self.atlas.spot[ends[1]]) > P.pair_km:
            return None
        hop = self.atlas.minutes[ends] if ends[0] != ends[1] else 0
        drive = self.atlas.drive(first) + hop + self.atlas.drive(second)
        if drive > P.pair_max_h * HOUR:
            return None
        ready = max(self.now + 30, first["pickup"]["window"]["from"])  # no car is collected before it is ready
        for start, _ in spans(first["pickup"]["hours"], ready, x["lastPickupAt"]):  # each day x can still be collected
            then = max(start + self.atlas.drive(first) + hop, second["pickup"]["window"]["from"])
            if first_open(second["pickup"]["hours"], then, y["lastPickupAt"]) is not None:  # y is ready and its yard open, in time: the same day or a later one
                return drive
        return None

    def pair(self, order: Order) -> bool:
        """Looks for a partner for a new car among our cars that wait.
        True when the new car is taken care of: in a gig with a partner, or held back to wait for one."""
        if self.now // DAY % 7 >= 4 and not P.pair_friday:
            return False
        waiting = [self.orders[o] for o in self.orders if o != order["id"] and (o in self.held or self.waits(o)) and self.plain(self.orders[o])]
        chains = [(x, y) for other in waiting for x, y in ((other, order), (order, other)) if self.chain(x, y) is not None]
        if chains:  # first a partner that no driver has seen yet (a gig that has sat makes drivers wait); then the pair that ends nearest to where it starts
            spot = self.atlas.spot
            fresh = lambda pair: all(o["id"] == order["id"] or o["id"] in self.held for o in pair)
            home = lambda pair: crow_km(spot[pair[1]["legs"][0]["delivery"]["placeId"]], spot[pair[0]["legs"][0]["pickup"]["placeId"]])
            x, y = min(chains, key=lambda pair: (not fresh(pair), home(pair), pair[0]["lastPickupAt"]))
            return self.together(x, y, order)
        if P.pair_hold and order["lastPickupAt"] - self.now >= max(6 * HOUR, 12 * P.pair_hold):  # the wait is a small part of the car's room
            self.held[order["id"]] = self.now + int(P.pair_hold)
            self.timers.append((self.held[order["id"]], "post", order["id"]))
            return True
        return False

    def together(self, x: Order, y: Order, new: Order) -> bool:
        """One gig for x and then y. False when the partner's own gig could not be taken out of the app (a driver took it this minute):
        then the new car still needs a gig. Refused by the world, both go alone."""
        for order in (x, y):
            self.held.pop(order["id"], None)
            gigs = self.gigs_of(order["id"])
            if gigs:
                self.outbox += [{"type": "withdraw", "gigId": gig} for gig in gigs]
                self.send()
                if any(action["type"] == "withdraw" for action, _ in self.refused):
                    return False
                self.leg_gigs.pop(order["id"], None)
        typical = sum(self.requests[order["id"]]["referenceFeeCents"] for order in (x, y))
        multiple = P.pair_small if typical < P.pair_small_eur * 100 else P.pair_fee
        stops = self.stops(x, [0], starter.Retry()) + self.stops(y, [0], starter.Retry())
        self.outbox.append({"type": "post", "stops": starter.without_windows(stops, self.now), "audience": {"experienced": False, "manualLicence": False},
                            "schedule": [{"at": self.now, "feeCents": max(1, int(typical * multiple + 0.5))}]})
        self.send()
        gig = self.leg_gigs.get(x["id"], {}).get(0)
        if gig is None or self.leg_gigs.get(y["id"], {}).get(0) != gig:  # the world would not have it
            self.tried.update((x["id"], y["id"]))
            for order in (x, y):
                if not self.gigs_of(order["id"]):
                    self.post(order, [0])
            return True
        self.partner[x["id"]], self.partner[y["id"]] = y["id"], x["id"]
        self.timers.append((self.now + int(P.pair_wait), "split", gig))
        return True

    def owners(self, gig_id: str) -> list[str]:
        """The orders that a gig still carries."""
        action = self.posts.get(gig_id)
        stops = [] if action is None else [s for s in action["stops"] if self.leg_gigs.get(s["orderId"], {}).get(s["leg"]) == gig_id]
        return list(dict.fromkeys(s["orderId"] for s in stops))

    def split(self, gig_id: str) -> None:
        """A two-car gig that found no driver is taken out of the app, and its cars go alone."""
        orders = self.owners(gig_id)
        if len(orders) < 2 or gig_id in self.booked:
            return
        self.outbox.append({"type": "withdraw", "gigId": gig_id})
        self.send()
        if not any(action.get("gigId") == gig_id for action, _ in self.refused):  # refused: a driver took it this minute
            self.apart(orders)

    def apart(self, orders: list[str]) -> None:
        """The cars of a two-car gig that is gone each get a gig of their own."""
        for order_id in orders:
            self.leg_gigs.pop(order_id, None)
            self.partner.pop(order_id, None)
            self.tried.add(order_id)
        for order_id in orders:
            if order_id in self.orders:
                self.post(self.orders[order_id], starter.undelivered(self.orders[order_id]))

    def tick(self) -> None:
        """Does what has come due: a two-car gig without a driver is split, a car held back for a partner is posted alone."""
        due = [timer for timer in self.timers if timer[0] <= self.now]
        self.timers = [timer for timer in self.timers if timer[0] > self.now]
        for _, what, key in due:
            if what == "split":
                self.split(key)
            elif what == "morning":
                self.again()
            elif what == "renew":
                self.renew(key)
            elif what == "last call":  # every car that is late and still waits, at the fee of last resort
                self.last_call = True
                self.renew(*[o for o in self.orders if self.waits(o) and self.now > self.orders[o]["lastPickupAt"]])
            elif key in self.held and key in self.orders:
                del self.held[key]
                self.post(self.orders[key], starter.undelivered(self.orders[key]))

    def rescue(self) -> None:
        """A car that waits with no gig at all (the world refused its post) gets a gig without windows of its own: the world always takes that."""
        if self.rescued_at == self.now:  # once a minute is enough
            return
        self.rescued_at = self.now
        pending = {stop["orderId"] for action in self.outbox if action["type"] == "post" for stop in action["stops"]}
        for order_id, order in list(self.orders.items()):
            legs = [leg for leg in starter.undelivered(order) if leg not in self.leg_gigs.get(order_id, {})]
            if legs and order_id not in self.held and order_id not in pending and self.rescued.get(order_id, 0) < 5:
                self.rescued[order_id] = self.rescued.get(order_id, 0) + 1
                stops = [{key: value for key, value in stop.items() if key != "window"} for stop in self.stops(order, legs, starter.Retry())]
                audience = {"experienced": any(leg["car"]["premium"] for leg in order["legs"]), "manualLicence": self.note(self.requests[order_id])["manual"]}
                self.outbox.append({"type": "post", "stops": stops, "audience": audience, "schedule": self.fees_for(order, len(legs))})

    def again(self) -> None:
        """A working morning: the cars that have waited since an earlier day come back as new gigs, so that the day's drivers hear of them."""
        today = self.now // DAY * DAY
        self.renew(*[o for o in self.orders if self.waits(o) and o not in self.urgent and self.steps.get(o) and self.steps[o][0][0] < today
                     and self.orders[o]["lastPickupAt"] > self.now + 4 * HOUR])

    def renew(self, *order_ids: str) -> list[str]:
        """These orders' gigs without a driver leave the app and come back as new gigs, at the fees that fit now. Returns the orders it did so for."""
        gigs = {o: self.gigs_of(o)[0] for o in order_ids if o in self.orders and len(self.gigs_of(o)) == 1 and o not in self.partner}
        gigs = {o: gig for o, gig in gigs.items() if gig not in self.booked and len(self.owners(gig)) == 1}
        self.outbox += [{"type": "withdraw", "gigId": gig} for gig in gigs.values()]
        self.send()
        kept = {refused.get("gigId") for refused, _ in self.refused}  # a driver took it this minute
        renewed = [o for o, gig in gigs.items() if gig not in kept]
        for order_id in renewed:
            action, order = self.posts[gigs[order_id]], self.orders[order_id]
            self.leg_gigs.pop(order_id, None)
            self.post(order, starter.undelivered(order), starter.Retry(manual_licence=action["audience"]["manualLicence"], plates=any(s.get("withPlates") for s in action["stops"])))
        return renewed

    def lost(self, order_id: str) -> None:
        """A car whose driver is gone: its gig comes back as new at once, and after a night once more at seven."""
        self.dropped.add(order_id)
        self.unlucky.add(order_id)
        self.renew(order_id)
        minute = self.now % DAY
        if not 7 * HOUR <= minute < 22 * HOUR:  # by night: once more at seven, when the day's drivers look
            timer = ((self.now // DAY + (minute >= 22 * HOUR)) * DAY + 7 * HOUR, "renew", order_id)
            self.timers += [timer] if timer not in self.timers else []

    def raise_fees(self, order_id: str) -> None:
        """From its deadline warning on, a car without a driver goes at the urgent fee, as a new gig."""
        self.urgent.add(order_id)
        posted_now = bool(self.steps.get(order_id)) and self.steps[order_id][0][0] == self.now  # it left a two-car gig this minute
        if not P.fresh or posted_now or not self.renew(order_id):
            super().raise_fees(order_id)

    def next_timer(self) -> int:
        return min((minute for minute, _, _ in self.timers), default=END)

    def send(self) -> None:
        self.tick()  # the live loop sends every turn, also when no event came: timers run there
        super().send()

    def read_results(self, actions, results) -> None:
        super().read_results(actions, results)
        self.refused = [(action, result) for action, result in zip(actions, results) if result["ok"] is not True]
        for action, _ in self.refused:
            self.refusals[action["type"]] = self.refusals.get(action["type"], 0) + 1

    def withdraw(self, order_id: str) -> bool:
        if order_id in self.partner and not any(gig in self.booked for gig in self.gigs_of(order_id)):  # a change of plan for one car of two: both go alone
            for gig in self.gigs_of(order_id):
                self.split(gig)
        return super().withdraw(order_id)

    # ------------------------------------------------------------------ restart
    def remember(self, line: dict) -> None:
        """Writes down what the world will not tell us again: our quotes, and what the model said of an order when we posted it."""
        if self.journal:
            os.makedirs(os.path.dirname(self.journal), exist_ok=True)
            with open(self.journal, "a", encoding="utf-8") as out:
                out.write(json.dumps(line) + "\n")

    def carry(self, action, gig_id: str) -> None:
        super().carry(action, gig_id)
        owners = list(dict.fromkeys(stop["orderId"] for stop in action["stops"]))
        if len(owners) == 1 and owners[0] not in self.steps and owners[0] in self.requests:  # a gig met after a restart: the fees it shows
            request = self.requests[owners[0]]
            typical = request["referenceFeeCents"] * starter.pickups(action) / len(request["legs"])
            self.steps[owners[0]] = [(step["at"], step["feeCents"] / typical) for step in action["schedule"]]
            if P.fresh:
                self.timers += [(step["at"], "renew", owners[0]) for step in action["schedule"][1:] if step["at"] > self.now]
        if len(owners) == 2 and owners[0] not in self.partner:  # a two-car gig met after a restart
            self.partner[owners[0]], self.partner[owners[1]] = owners[1], owners[0]
            self.timers.append((self.now + int(P.pair_wait), "split", gig_id))

    def rejoin(self, snapshot, history) -> None:
        """After a restart the dealer side is replayed: every answer and every arrival of the week, in order, against the quotes in the journal.
        Then the starter rebuilds orders and gigs from the world and answers what was missed."""
        quotes, lines = {}, []
        if self.journal and os.path.exists(self.journal):
            with open(self.journal, encoding="utf-8") as f:
                lines = [json.loads(line) for line in f if line.strip()]
        for line in lines:
            if "quote" in line:
                quotes[line["quote"]] = line["multiples"]
        self.requests = {e["request"]["id"]: e["request"] for e in history if e["kind"] == "price_request"}
        self.orders = {o["id"]: {**o, "deliveredAt": [None] * len(o["legs"])} for o in snapshot["orders"] if o["id"] in self.requests and o["status"] != "cancelled"}
        for event in sorted(history, key=lambda e: e["seq"]):
            answered = event["order"]["id"] if event["kind"] == "order_won" else event["requestId"] if event["kind"] == "order_lost" else None
            if answered in quotes:
                self.quoted[answered] = quotes[answered]
            self.fold(event)
            if event["kind"] == "delivered" and event["orderId"] in self.orders:
                self.orders[event["orderId"]]["deliveredAt"][event["leg"]] = event["at"]
        self.won = len(self.orders)
        self.forecast = {line["forecast"]: line["logit"] for line in lines if "forecast" in line and line["forecast"] in self.orders}
        alone = {gig["id"]: gig["stops"][0]["orderId"] for gig in snapshot["gigs"] if len({stop["orderId"] for stop in gig["stops"]}) == 1}
        self.unlucky = {alone[event["gigId"]] for event in history if event["kind"] in ("gig_dropped", "no_show") and event["gigId"] in alone}
        super().rejoin(snapshot, history)

    def arrived(self, order: Order) -> None:
        """An order's last car has arrived: on time, the dealer trusts us one order more; late, half as much."""
        noted = self.note(self.requests[order["id"]])["deadline_at"]
        on_time = max(order["deliveredAt"]) <= min(order["deadline"], noted or order["deadline"])
        self.ended[order["id"]] = on_time
        count = self.trust.get(order["dealerId"], 0)
        self.trust[order["dealerId"]] = min(25, count + 1) if on_time else count // 2

    # ------------------------------------------------------------------ events
    def fold(self, event) -> None:
        """What an event teaches the desk about dealers: a yes or a no moves the price level, an arrival moves the dealer's trust.
        The same after a restart, when the week's events are read again."""
        kind = event["kind"]
        if kind == "order_won":
            self.learn(event["order"]["id"], event["order"]["option"])
        elif kind == "order_lost":
            self.learn(event["requestId"], None)
        elif kind == "delivered" and event["orderId"] in self.orders:
            order = self.orders[event["orderId"]]
            if all(at is not None or leg == event["leg"] for leg, at in enumerate(order["deliveredAt"])):  # the order's last car
                self.arrived({**order, "deliveredAt": [event["at"] if leg == event["leg"] else at for leg, at in enumerate(order["deliveredAt"])]})
        elif kind == "ledger" and event["line"]["kind"] == "late_refund" and self.ended.get(event["line"].get("orderId")):
            order = self.orders[event["line"]["orderId"]]  # the world says it was late after all
            self.ended[order["id"]] = False
            self.trust[order["dealerId"]] = max(0, self.trust.get(order["dealerId"], 0) - 1) // 2

    def handle(self, event) -> None:
        kind = event["kind"]
        self.tick()
        self.rescue()
        if kind == "order_won":
            self.won += 1
        elif kind == "order_cancelled" and event["orderId"] in self.orders:
            self.won -= 1
            self.forecast.pop(event["orderId"], None)
        elif kind == "gig_booked":
            self.dropped.difference_update(self.owners(event["gigId"]))
        self.fold(event)
        shared = self.partner.get(event.get("orderId", ""))  # the other car of a two-car gig that this event is about
        if shared and kind == "deadline_close":  # no driver, and time is short: both cars go alone, this one at the urgent fee
            self.urgent.add(event["orderId"])
            for gig in self.gigs_of(event["orderId"]):
                self.split(gig)
        super().handle(event)
        if kind in ("gig_dropped", "no_show") and len(self.owners(event["gigId"])) > 1:  # the driver of two cars is gone: they go alone
            self.dropped.update(self.owners(event["gigId"]))
            self.split(event["gigId"])
        elif kind in ("gig_dropped", "no_show") and P.fresh:
            for order_id in self.owners(event["gigId"]):
                self.lost(order_id)
        elif shared and kind in ("delivered", "visit_failed"):  # one car is out of the gig: the other is on its own in it
            self.partner.pop(event["orderId"], None)
            self.partner.pop(shared, None)
        elif shared and kind == "order_cancelled":
            self.partner.pop(event["orderId"], None)
            self.partner.pop(shared, None)
            gone = {gig["gigId"] for gig in event["gigs"] if gig["outcome"] in ("withdrawn", "released")}
            if shared in self.orders and any(gig in gone for gig in self.gigs_of(shared)):  # the gig went with the cancelled car: the other needs a new one
                self.apart([shared])

    # ------------------------------------------------------------------ measuring the world
    def dice(self, key: str) -> random.Random:
        """A die of its own for each request of each world: the same again on a rerun of the same world."""
        return random.Random(zlib.crc32((self.world.id + key).encode()))

    def quote_explore(self, request: PriceRequest) -> None:
        """A random 1.0-1.9 x list on a random subset of the options; orders with two cars are declined."""
        dice, options = self.dice(request["id"]), request["options"]
        if len(request["legs"]) > 1:
            prices = {options[0]["kind"]: options[0]["listPriceCents"] * DECLINE}
        else:
            chosen = [o for o in options if dice.random() < 0.5] or [dice.choice(options)]
            prices = {o["kind"]: euros(o["listPriceCents"] * dice.uniform(P.explore_lo, P.explore_hi)) for o in chosen}
        self.outbox.append({"type": "quote", "requestId": request["id"], "prices": prices})


def play_practice(world, level: int) -> "Desk":
    """The starter's practice loop, with one addition: the clock also stops at the desk's next timer."""
    snapshot = world.snapshot()
    desk, ends_at = starter.Desk(world, level, snapshot["now"]), snapshot["endsAt"]
    while desk.now < ends_at:
        day, midnight = desk.now // DAY, (desk.now // DAY + 1) * DAY
        desk.tick()
        actions, desk.outbox = desk.outbox, []
        step = world.advance(until=starter.WAKE_ON, max=min(ends_at, midnight, max(desk.now + 1, desk.next_timer())), actions=actions)
        desk.read_results(actions, step["results"])
        desk.now = step["now"]
        for event in step["events"]:
            desk.handle(event)
        if desk.now // DAY > day:
            starter.report(starter.WEEKDAYS[day % 7], world.score())
    return desk


def play_final(world) -> None:
    """The starter's loop for the final, with one change: answers that are due together go out in one send. Requests come many at once, and
    each has 15 minutes of the world's clock, which is 4.5 real seconds: a send for each would use them up."""
    history, snapshot = world.events(), world.snapshot()
    if snapshot["now"] >= snapshot["endsAt"]:
        return
    level = next((w["level"] for w in world.client.worlds() if w["worldId"] == world.id), 8)
    desk = starter.Desk(world, level, snapshot["now"])
    desk.rejoin(snapshot, history)
    desk.send()
    waiting, clock = None, 0.0  # since when an answer waits in the outbox; when the world's clock was last read
    for event in world.stream(after=history[-1]["seq"] if history else -1, idle=0.2):
        day = desk.now // DAY
        if event is not None:
            desk.now = max(desk.now, event["at"])
            desk.handle(event)
        elif time.time() - clock >= 1.0:
            desk.now, clock = max(desk.now, world.client.final()["now"]), time.time()
        waiting = waiting or (time.time() if desk.outbox else None)
        if event is None or len(desk.outbox) >= 20 or (waiting and time.time() - waiting >= 0.3):  # the stream is quiet, or the answers have waited enough
            desk.send()  # also when nothing waits: the desk's timers run there
            waiting = None
        if desk.now // DAY > day:
            starter.report(starter.WEEKDAYS[day % 7], world.score())
        if desk.now >= snapshot["endsAt"]:
            return


def week_in_numbers(desk: "Desk", events: list) -> str:
    """One line about a finished practice week, for sweep.py: what the drivers were paid against the typical fees, alone and two cars a gig,
    and what the dealers paid against the list prices."""
    paid: dict[str, int] = {}
    for event in events:
        if event["kind"] == "ledger" and event["line"]["kind"] == "driver_fee" and event["line"].get("gigId"):
            paid[event["line"]["gigId"]] = paid.get(event["line"]["gigId"], 0) - event["line"]["cents"]
    sums = {1: [0, 0, 0], 2: [0, 0, 0]}  # cars in the gig -> fees paid, typical fees, cars
    for gig, cents in paid.items():
        action = desk.posts.get(gig)
        orders = [] if action is None else list(dict.fromkeys(stop["orderId"] for stop in action["stops"]))
        if orders and all(order in desk.requests and len(desk.requests[order]["legs"]) == 1 for order in orders):
            row = sums[min(2, len(orders))]
            row[0], row[1], row[2] = row[0] + cents, row[1] + sum(desk.requests[order]["referenceFeeCents"] for order in orders), row[2] + len(orders)
    price = sum(order["priceCents"] for order in desk.orders.values())
    listed = sum(desk.list_price(order) for order in desk.orders.values())
    cars = max(1, sums[1][2] + sums[2][2])
    return (f"Week: fees x{(sums[1][0] + sums[2][0]) / max(1, sums[1][1] + sums[2][1]):.3f} typical, one car x{sums[1][0] / max(1, sums[1][1]):.3f}, "
            f"two cars x{sums[2][0] / max(1, sums[2][1]):.3f}, paired {sums[2][2] / cars:.0%} of cars, prices x{price / max(1, listed):.3f} list"
            f" | refused {desk.refusals}, rescued {len(desk.rescued)}, outage days {[day for day, towns in desk.down.items() if sum(towns.values()) > 0.5]}")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--param", action="append", default=[], metavar="name=value")
    args, rest = parser.parse_known_args()
    names = {f.name for f in fields(Params)}
    measured(load_model())
    for item in args.param:
        name, _, value = item.partition("=")
        if name not in names:
            sys.exit(f"No parameter '{name}'. There are: {', '.join(sorted(names))}")
        old = getattr(P, name)
        setattr(P, name, value.lower() in ("1", "true", "yes") if isinstance(old, bool) else value.replace(";", ",") if isinstance(old, str) else type(old)(float(value)))
    print(f"Params: {P}", flush=True)
    starter.Desk = Desk  # the starter plays with our desk
    seed = rest[rest.index("--seed") + 1] if "--seed" in rest else "noseed"
    tag = re.sub(r"[^A-Za-z0-9=.,;_-]", "", ",".join(args.param)) or "base"
    play = play_practice

    def play_and_save(world, level):
        """After a practice week: keep everything about it in runs/, for fit.py and for the slides."""
        desk = play(world, level)
        saved = {"seed": seed, "level": level, "params": vars(P), "worldId": world.id, "opened": desk.opened, "pairs": sorted(desk.tried), "trace": desk.trace}
        for name, read in (("score", world.score), ("events", world.events), ("roster", world.roster), ("snapshot", world.snapshot), ("reveal", world.reveal)):
            try:
                saved[name] = read()
            except Exception as error:  # a ranking week cannot be revealed
                saved[name] = None
                print(f"Not saved: {name}: {error}", flush=True)
        if saved.get("events"):
            saved["events"] = [e for e in saved["events"] if e["kind"] != "gig_viewed"]  # the views are most of a week's bytes, and nothing of ours reads them
        if saved.get("reveal"):
            saved["reveal"].pop("views", None)
        if saved.get("events"):
            print(week_in_numbers(desk, saved["events"]), flush=True)
        os.makedirs("runs", exist_ok=True)
        path = os.path.join("runs", f"L{level}_{seed if seed != 'noseed' else world.id}_{tag}.json.gz")
        with gzip.open(path, "wt", encoding="utf-8") as out:
            json.dump(saved, out)
        print(f"Saved {path}", flush=True)

    starter.play_practice, starter.play_final = play_and_save, play_final
    sys.argv = [sys.argv[0]] + rest
    starter.main()


if __name__ == "__main__":
    main()
