"""Shared routing data, site opening hours, and driver locations for a world.
These determine the pickup window and how hard it will be to find a driver.

The dispatcher (dispatch.py) and offline model fitting (fit.py) use the same calculations.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Optional

HOUR, DAY = 60, 1440
NEAR_KM = 30       # the app notifies drivers who live within 30 km of pickup about new gigs (RULES.md)
CHARGING = 40      # minutes per charging stop (RULES.md)
PLATES = 30        # minutes to fit license plates (RULES.md)


def crow_km(a: tuple, b: tuple) -> float:
    """Straight-line distance in km between two latitude and longitude pairs."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def open_span(hours: Optional[dict], day: int) -> Optional[tuple]:
    """The site's opening interval in minutes on day `day` (0 is Monday). Private addresses have no opening hours."""
    if hours is None:
        return day * DAY, (day + 1) * DAY
    weekday = day % 7
    if weekday in hours["weekdays"]:
        return day * DAY + hours["opens"], day * DAY + hours["closes"]
    if weekday == 5 and hours.get("saturday"):
        return day * DAY + hours["saturday"]["opens"], day * DAY + hours["saturday"]["closes"]
    return None


def last_open(hours: Optional[dict], until: int, since: int = 0) -> Optional[int]:
    """Latest minute in [since, until] when the site is open."""
    day = until // DAY
    while day >= 0 and (day + 1) * DAY > since:
        span = open_span(hours, day)
        if span and span[0] <= until:
            minute = min(until, span[1])
            return minute if minute >= since else None
        day -= 1
    return None


def first_open(hours: Optional[dict], since: int, until: int) -> Optional[int]:
    """Earliest minute in [since, until] when the site is open."""
    day = since // DAY
    while day * DAY <= until:
        span = open_span(hours, day)
        if span and span[1] > since:
            minute = max(since, span[0])
            return minute if minute <= until else None
        day += 1
    return None


def open_minutes(hours: Optional[dict], since: int, until: int) -> int:
    """Number of minutes the site is open in [since, until]."""
    total, day = 0, since // DAY
    while day * DAY <= until:
        span = open_span(hours, day)
        if span:
            total += max(0, min(until, span[1]) - max(since, span[0]))
        day += 1
    return total


class Atlas:
    """The world's map and driver roster."""

    def __init__(self, world_map: dict, roster: list):
        self.minutes = {(r["from"], r["to"]): r["minutes"] for r in world_map["roads"]}
        self.km = {(r["from"], r["to"]): r["km"] for r in world_map["roads"]}
        self.spot = {p["id"]: (p["lat"], p["lon"]) for p in world_map["places"]}
        homes = Counter(d["homePlaceId"] for d in roster)
        seasoned = Counter(d["homePlaceId"] for d in roster if d["rating"] >= 4.8 and d["completedGigs"] >= 50)
        self.near = {p: sum(n for h, n in homes.items() if crow_km(self.spot[h], self.spot[p]) <= NEAR_KM) for p in self.spot}
        self.near_seasoned = {p: sum(n for h, n in seasoned.items() if crow_km(self.spot[h], self.spot[p]) <= NEAR_KM) for p in self.spot}
        self.region = {p: sum(n for h, n in homes.items() if crow_km(self.spot[h], self.spot[p]) <= 120) for p in self.spot}
        self.reach = {p: {q for q in self.spot if crow_km(self.spot[p], self.spot[q]) <= 80} for p in self.spot}  # a town's region: where an outage centred on it reaches
        self.drivers = len(roster)

    def drive(self, leg: dict) -> int:
        """Driving minutes from pickup to delivery, including any required EV charging stop."""
        ends = (leg["pickup"]["placeId"], leg["delivery"]["placeId"])
        return self.minutes[ends] + (CHARGING if self.needs_charging(leg) else 0)

    def needs_charging(self, leg: dict) -> bool:
        car = leg["car"]
        return bool(car["electric"] and car["chargePercent"] is not None and car["chargePercent"] < 30
                    and self.km[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])] > 200)

    def last_pickup(self, leg: dict, deadline: int, pickup_closes: Optional[int] = None, delivery_closes: Optional[int] = None,
                    extra_minutes: int = 0) -> Optional[int]:
        """Latest pickup minute that still meets `deadline`, using opening hours at both sites.
        pickup_closes and delivery_closes are the actual closing minutes of the day when the note gives earlier hours."""
        arrive = last_open(self.narrowed(leg["delivery"]["hours"], None, delivery_closes), deadline)
        if arrive is None:
            return None
        latest = arrive - self.drive(leg) - extra_minutes
        if leg["pickup"]["privateAddress"]:
            latest = min(latest, leg["pickup"]["window"]["to"])
        return last_open(self.narrowed(leg["pickup"]["hours"], None, pickup_closes), latest)

    @staticmethod
    def narrowed(hours: Optional[dict], opens: Optional[int], closes: Optional[int]) -> Optional[dict]:
        """Opening hours narrowed by the dealer's note."""
        if hours is None or (opens is None and closes is None):
            return hours
        out = dict(hours)
        if opens is not None:
            out["opens"] = max(hours["opens"], opens)
        if closes is not None:
            out["closes"] = min(hours["closes"], closes)
        if hours.get("saturday"):
            sat = dict(hours["saturday"])
            if opens is not None:
                sat["opens"] = max(sat["opens"], opens)
            if closes is not None:
                sat["closes"] = min(sat["closes"], closes)
            out["saturday"] = sat if sat["opens"] < sat["closes"] else None
        return out if out["opens"] < out["closes"] else hours

    def signs(self, request: dict, last_pickup: int, at: int, ready: Optional[int] = None) -> dict:
        """Features that indicate how hard it is to find a driver on time, measured at minute `at`."""
        leg = request["legs"][0]
        pickup, delivery = leg["pickup"]["placeId"], leg["delivery"]["placeId"]
        km = self.km[(pickup, delivery)]
        start = max(at, ready or 0, leg["pickup"]["window"]["from"] if leg["pickup"]["privateAddress"] else 0)
        room = open_minutes(leg["pickup"]["hours"], start, last_pickup) / HOUR  # hours the pickup site is still open before the last pickup
        return {
            "one": 1.0,
            "slack": math.log1p(max(0.0, (last_pickup - at) / HOUR)),
            "tight": float(last_pickup - at < 8 * HOUR),   # under eight hours: hard at any fee
            "day_left": float(8 * HOUR <= last_pickup - at < 24 * HOUR),
            "room": math.log1p(max(0.0, room)),
            "short": float(km < 40),
            "long": min(max(km, 100.0), 800.0) / 100 - 1,
            "near_pickup": math.log1p(self.near[pickup]),
            "near_delivery": math.log1p(self.near[delivery]),
            "region": math.log1p(self.region[pickup]),
            "private_pickup": float(leg["pickup"]["privateAddress"]),
            "private_delivery": float(leg["delivery"]["privateAddress"]),
            "premium": float(any(l["car"]["premium"] for l in request["legs"])),
            "seasoned": float(any(l["car"]["premium"] for l in request["legs"])) * math.log1p(self.near_seasoned[pickup]),
            "pay": math.log(request["referenceFeeCents"] / len(request["legs"]) / request["options"][0]["listPriceCents"]),
            "friday": float(at // DAY % 7 == 4 and at % DAY >= 12 * HOUR),
            "ends_friday": float(last_pickup // DAY % 7 == 4),  # a car that must be collected on a Friday: the day fewest drivers take a low fee
            "today": float(last_pickup // DAY == request["arrivedAt"] // DAY),  # a car asked for today: the drivers who work today see it new
            "note": float(bool(request.get("note"))),
        }


def with_fee(signs: dict, multiple: float) -> dict:
    """The signs of a car together with the fee its gig opens at, in typical fees. The fee counts in three stretches, in steps of 0.15:
    up to 0.85, from there to the typical fee, and beyond it. The typical fee is a threshold: the app tells drivers of a gig once,
    when it is new, so a gig that opens under it loses drivers fast and a gig that opens over it gains few."""
    low, mid, high = min(multiple - 0.85, 0.0) / 0.15, min(max(multiple - 0.85, 0.0), 0.15) / 0.15, max(multiple - 1.0, 0.0) / 0.15
    fee = {"low": low, "mid": mid, "high": high}
    fee.update({f"{stretch}_{sign}": fee[stretch] * signs[sign] for stretch in ("low", "mid") for sign in ("slack", "long", "short", "ends_friday")})  # what a low fee does to this kind of car
    return dict(signs, **fee)


WORK = (8 * HOUR, 18 * HOUR)  # the hours of a weekday in which dealers send requests and most drivers book


def work_after(minute: int, minutes: int) -> int:
    """The minute at which `minutes` of working time (Monday to Friday, 8 to 18) have passed since `minute`."""
    day = minute // DAY
    while True:
        if day % 7 < 5:
            start, end = max(minute, day * DAY + WORK[0]), day * DAY + WORK[1]
            if end - start >= minutes:
                return start + minutes
            minutes -= max(0, end - start)
        day += 1


def work_before(minute: int, minutes: int) -> int:
    """The minute from which `minutes` of working time (Monday to Friday, 8 to 18) remain until `minute`."""
    day = minute // DAY
    while day >= 0:
        if day % 7 < 5:
            start, end = day * DAY + WORK[0], min(minute, day * DAY + WORK[1])
            if end - start >= minutes:
                return end - minutes
            minutes -= max(0, end - start)
        day -= 1
    return 0
