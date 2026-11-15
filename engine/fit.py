"""Fit models on the weeks saved in runs/ and write the parameters to model.json for the bot.

    python fit.py                 # read runs/*.json.gz, print the tables, and write model.json
    python fit.py --only explore  # use only weeks whose filenames contain 'explore'

Two models:
  1. On-time delivery probability from the driver fee and car features (world.Atlas.signs).
  2. Dealer acceptance price by day, delivery site, pickup site, delivery speed, and trust.
This script generates all values in model.json.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import os
import random
import sys
import zlib
from collections import Counter, defaultdict

import numpy as np

from world import DAY, HOUR, Atlas, with_fee

FEES = (0.7, 0.85, 1.0, 1.15, 1.3, 1.5)
PLAYED_SLOPE = 12.0  # the learner's slope in play. The slope that predicts dealers' answers best is 14 to 16, but the week is bound by drivers, not by
#                      dealers: a flatter curve asks for more margin an order, and in played weeks 12 earned EUR 700 to 1,150 a week more than 14 and 16.
CAR_SIGNS = ["one", "slack", "day_left", "room", "short", "long", "near_pickup", "near_delivery", "region", "private_pickup", "private_delivery",
             "premium", "pay", "friday", "ends_friday", "today", "backlog"]
FEE_SIGNS = ["low", "mid", "high", "low_slack", "mid_slack", "low_long", "mid_long", "low_short", "mid_short"]  # the opening fee in three stretches (world.with_fee)
ON_TIME_SIGNS = CAR_SIGNS + FEE_SIGNS


def load(path: str) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        run = json.load(f)
    run["path"] = path
    return run


def explore_fee(world_id: str, order_id: str) -> float:
    """Random opening fee drawn by dispatch.py for this order, using the same draw."""
    return random.Random(zlib.crc32((world_id + "fee" + order_id).encode())).choice(FEES)


def orders_table(run: dict, atlas: Atlas) -> list:
    """One row per won order that was not canceled, with features at the time of the win, fees, and outcomes."""
    events, reveal, params = run["events"], run["reveal"], run["params"]
    explore = bool(params.get("explore"))
    requests = {r["request"]["id"]: r["request"] for r in reveal["requests"]}
    gig_order: dict = {}
    for gig in (run.get("snapshot") or {}).get("gigs", []):
        gig_order[gig["id"]] = gig["stops"][0]["orderId"]
    won, cancelled, warned, late, delivered, booked_at, failed, refunds, fees = {}, set(), {}, set(), {}, {}, Counter(), Counter(), Counter()
    shared = {gig["id"] for gig in (run.get("snapshot") or {}).get("gigs", []) if len({stop["orderId"] for stop in gig["stops"]}) > 1}  # two-car gigs
    for e in events:
        k = e["kind"]
        if k in ("picked_up", "delivered", "visit_failed"):
            gig_order.setdefault(e["gigId"], e["orderId"])
    for e in events:
        k = e["kind"]
        if k == "order_won":
            won[e["order"]["id"]] = (e["at"], e["order"])
        elif k == "order_cancelled":
            cancelled.add(e["orderId"])
        elif k == "deadline_close":
            warned.setdefault(e["orderId"], e["at"])
        elif k == "delivered":
            delivered[e["orderId"]] = e["at"]
        elif k == "visit_failed":
            failed[e["orderId"]] += 1
        elif k == "gig_booked" and e["gigId"] in gig_order:
            booked_at.setdefault(gig_order[e["gigId"]], e["at"])
        elif k == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId"):
            late.add(e["line"]["orderId"])
            refunds[e["line"]["orderId"]] -= e["line"]["cents"]
        elif k == "ledger" and e["line"]["kind"] == "driver_fee" and e["line"].get("gigId") not in shared:
            owner = e["line"].get("orderId") or gig_order.get(e["line"].get("gigId"))
            if owner:
                fees[owner] -= e["line"]["cents"]
    opened = run.get("opened") or {}  # order -> the fee multiple its first gig opened at, as the desk wrote it down

    def posted_fee(oid: str) -> float:
        """First gig's opening fee as a multiple of typical. The snapshot holds the final schedule, which shows the urgent fee after the warning."""
        if explore:
            return explore_fee(run["worldId"], oid)
        return float(opened[oid]) if oid in opened else float(params.get("fee", 1.0))

    fee_of = {oid: posted_fee(oid) for oid in won}
    order_ids = sorted(won, key=lambda oid: won[oid][0])
    rows = []
    for oid in order_ids:
        at, order = won[oid]
        if oid in cancelled or len(order["legs"]) != 1 or oid not in requests:
            continue
        if not explore and opened and oid not in opened:  # it never had a gig of its own (it went in a two-car gig)
            continue
        request = requests[oid]
        waiting = [o for o in order_ids if o != oid and won[o][0] <= at and booked_at.get(o, 10 ** 9) > at and delivered.get(o, 10 ** 9) > at and o not in cancelled]
        level = (sum(fee_of[o] for o in waiting) + fee_of[oid]) / (len(waiting) + 1)
        signs = atlas.signs(request, order["lastPickupAt"], at)
        here = request["legs"][0]["pickup"]["placeId"]
        signs.update(backlog=math.log1p(len(waiting)), level=math.log(level), weekday=float(at // DAY % 7),
                     local=math.log1p(sum(1 for o in waiting if requests[o]["legs"][0]["pickup"]["placeId"] == here)))
        signs = with_fee(signs, fee_of[oid])
        on_time = oid in delivered and oid not in late
        option = next(o for o in request["options"] if o["kind"] == order["option"])
        paid = fees[oid] / request["referenceFeeCents"] if fees[oid] else None  # None: never delivered
        rows.append(dict(id=oid, world=run["worldId"], signs=signs, on_time=on_time, fee=fee_of[oid], explore=explore, paid=paid,
                         booked=oid in booked_at and (oid not in warned or booked_at[oid] < warned[oid]), refund=refunds[oid],
                         warned=oid in warned, failed=failed[oid], option=order["option"], slack_h=(order["lastPickupAt"] - at) / HOUR,
                         price=order["priceCents"], list=option["listPriceCents"], typical=request["referenceFeeCents"],
                         km=atlas.km[(request["legs"][0]["pickup"]["placeId"], request["legs"][0]["delivery"]["placeId"])],
                         near=atlas.near[request["legs"][0]["pickup"]["placeId"]], wait_h=(booked_at[oid] - at) / HOUR if oid in booked_at else None))
    return rows


def logistic(X: np.ndarray, y: np.ndarray, ridge: np.ndarray, start: np.ndarray | None = None, steps: int = 60) -> np.ndarray:
    """Logistic regression with a ridge penalty per coefficient, solved by Newton's method."""
    w = np.zeros(X.shape[1]) if start is None else start.copy()
    for _ in range(steps):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        grad = X.T @ (y - p) - ridge * w
        hess = (X * (p * (1 - p))[:, None]).T @ X + np.diag(ridge) + 1e-9 * np.eye(X.shape[1])
        step = np.linalg.solve(hess, grad)
        w += step
        if np.abs(step).max() < 1e-7:
            break
    return w


def fit_on_time(rows: list, names: list) -> dict:
    X = np.array([[r["signs"][n] for n in names] for r in rows])
    y = np.array([float(r["on_time"]) for r in rows])
    ridge = np.array([0.0 if n == "one" else 1.0 for n in names])
    w = logistic(X, y, ridge)
    p = 1 / (1 + np.exp(-X @ w))
    loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    base = -np.mean(y * np.log(y.mean()) + (1 - y) * np.log(1 - y.mean()))
    print(f"\nON-TIME MODEL: {len(rows)} orders, {y.mean():.1%} on time; log-loss {loss:.4f} (baseline: {base:.4f})")
    for n, v in zip(names, w):
        print(f"    {n:<18}{v:+.3f}")
    return {n: round(float(v), 4) for n, v in zip(names, w)}


PAID_SIGNS = CAR_SIGNS + FEE_SIGNS + ["low_ends_friday", "mid_ends_friday"]  # on a Friday a low opening fee ends up paying as much as the typical one


def fit_paid(rows: list) -> dict:
    """Predict the final fee as a multiple of typical using ridge regression on weeks that followed the bot's fee increases."""
    rows = [r for r in rows if r["paid"] is not None]
    X = np.array([[r["signs"][n] for n in PAID_SIGNS] for r in rows])
    y = np.array([min(r["paid"], 2.0) for r in rows])
    w = np.linalg.solve(X.T @ X + np.diag([0.0] + [0.3] * (len(PAID_SIGNS) - 1)), X.T @ y)
    err = float(np.sqrt(np.mean((X @ w - y) ** 2)))
    print(f"\nFEE PAID MODEL: {len(rows)} orders; average paid x{y.mean():.3f} typical, average opening x{np.mean([r['fee'] for r in rows]):.3f}; error {err:.3f}")
    for n, v in zip(PAID_SIGNS, w):
        print(f"    {n:<18}{v:+.3f}")
    groups = defaultdict(list)
    for r, p in zip(rows, X @ w):
        groups[round(r["fee"], 2)].append((r["paid"], p, r["on_time"]))
    for g in sorted(groups):
        v = groups[g]
        print(f"    opens at x{g:<5} n {len(v):>5}  actual paid x{sum(a for a, _, _ in v) / len(v):.3f}  modeled x{sum(b for _, b, _ in v) / len(v):.3f}  on time {sum(c for _, _, c in v) / len(v):6.1%}")
    return {n: round(float(v), 4) for n, v in zip(PAID_SIGNS, w)}


def calibration(rows: list, weights: dict, key, label: str) -> None:
    groups = defaultdict(list)
    for r in rows:
        logit = sum(weights[n] * r["signs"][n] for n in weights)
        groups[key(r)].append((1 / (1 + math.exp(-logit)), r["on_time"], r["booked"]))
    print(f"  {label}")
    for g in sorted(groups, key=lambda x: (isinstance(x, str), x)):
        v = groups[g]
        print(f"    {str(g):<14} n {len(v):>5}  actual on-time rate {sum(o for _, o, _ in v) / len(v):6.1%}  modeled {sum(p for p, _, _ in v) / len(v):6.1%}  booked before warning {sum(b for _, _, b in v) / len(v):6.1%}")


# ---------------------------------------------------------------------------------------------- dealers
def quotes_table(run: dict) -> list:
    """One row per single-option quote so the dealer's choice is known, with its price, outcome, and context."""
    events, reveal = run["events"], run["reveal"]
    won_at, deadline, dealer_of, noted = {}, {}, {}, {}
    for e in events:
        if e["kind"] == "order_won":
            o = e["order"]
            deadline[o["id"]], dealer_of[o["id"]] = o["deadline"], o["dealerId"]
    arrivals = []  # (minute, dealer, on time?) of every delivered order, to rebuild each dealer's trust
    late = {e["line"]["orderId"] for e in events if e["kind"] == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId")}
    for e in events:
        if e["kind"] == "delivered" and e["orderId"] in dealer_of:
            arrivals.append((e["at"], dealer_of[e["orderId"]], e["orderId"] not in late))
    arrivals.sort()
    rows, trust, k = [], Counter(), 0
    for r in sorted(reveal["requests"], key=lambda r: r["request"]["respondBy"]):
        request, quote = r["request"], r.get("quote")
        while k < len(arrivals) and arrivals[k][0] <= request["respondBy"]:
            _, dealer, on_time = arrivals[k]
            trust[dealer] = min(25, trust[dealer] + 1) if on_time else trust[dealer] // 2
            k += 1
        if not quote or len(request["legs"]) != 1:
            continue
        lists = {o["kind"]: o["listPriceCents"] for o in request["options"]}
        kinds = [o["kind"] for o in request["options"]]
        offered = {kind: price / lists[kind] for kind, price in quote.items() if price / lists[kind] < 3.5}
        if not offered:
            continue
        leg = request["legs"][0]
        rows.append(dict(world=run["worldId"], day=request["arrivedAt"] // DAY, dealer=request["dealerId"], to=leg["delivery"]["placeId"],
                         frm=leg["pickup"]["placeId"], offered=offered, kinds=kinds, lists=lists, won=r["outcome"] == "won", option=r.get("option"),
                         trust=trust[request["dealerId"]], typical=request["referenceFeeCents"], explore=bool(run["params"].get("explore")),
                         private=leg["delivery"]["privateAddress"] or leg["pickup"]["privateAddress"], premium=leg["car"]["premium"]))
    return rows


def asked(row: dict, kind: str, multiple: float, gaps: tuple) -> float:
    """An option's quote as the dealer weighs it. Add the euro discount per step to a slower option, then take the log of the multiple of the fastest option's list price
    (dispatch.Desk.asked)."""
    index = row["kinds"].index(kind)
    gap = sum(gaps[0] if k == "same_day" else gaps[1] for k in row["kinds"][:index])
    return math.log((multiple * row["lists"][kind] + gap * 100) / row["lists"][row["kinds"][0]])


def market_design(single: list, gaps: tuple) -> tuple:
    columns: dict = {}

    def column(name: str) -> int:
        return columns.setdefault(name, len(columns))

    data = []
    for r in single:
        (kind, multiple), = r["offered"].items()
        cols = [column("slope"), column("one"), column(f"world:{r['world']}"), column(f"day:{r['world']}:{r['day']}"), column(f"to:{r['to']}"),
                column(f"from:{r['frm']}"), column("trust")]
        data.append((cols, [-asked(r, kind, multiple, gaps), 1.0, 1.0, 1.0, 1.0, 1.0, float(r["trust"])], float(r["won"])))
    X = np.zeros((len(data), len(columns)))
    y = np.zeros(len(data))
    for i, (cols, values, won) in enumerate(data):
        X[i, cols] = values
        y[i] = won
    ridge = np.array([0.0 if name in ("slope", "one", "trust") else 4.0 if name.startswith("world") else 8.0 for name in columns])
    w = logistic(X, y, ridge)
    p = np.clip(1 / (1 + np.exp(-np.clip(X @ w, -30, 30))), 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), w, columns


def fit_market(rows: list, quiet: bool = False, gaps: tuple | None = None) -> dict:
    """Model dealer acceptance with a logistic curve in log price. The price level sums week, day, delivery site, pickup site, and trust.
    Fit the two fixed euro discounts for slower options."""
    single = [r for r in rows if len(r["offered"]) == 1]
    if gaps is None:
        gaps = (16.0, 9.0)
        for _ in range(2):  # two passes, one value at a time
            gaps = (min(range(6, 27), key=lambda d: market_design(single, (float(d), gaps[1]))[0]), gaps[1])
            gaps = (float(gaps[0]), float(min(range(0, 19), key=lambda d: market_design(single, (gaps[0], float(d)))[0])))
    loss, w, columns = market_design(single, gaps)
    y = np.array([float(r["won"]) for r in single])
    slope = w[columns["slope"]]
    part = lambda prefix: {name.split(":", 1)[1]: w[i] / slope for name, i in columns.items() if name.startswith(prefix + ":")}
    worlds, days, to, frm = part("world"), part("day"), part("to"), part("from")
    level = w[columns["one"]] / slope
    sd = lambda d: float(np.std(list(d.values()))) if d else 0.0
    if not quiet:
        print(f"\nDEALER MODEL: {len(single)} single-option quotes, win rate {y.mean():.1%}; log-loss {loss:.4f}")
        print(f"    slope {slope:.2f}; average level x{math.exp(level):.3f} list; trust {w[columns['trust']] / slope:+.4f} per on-time order")
        print(f"    slower options: dealers pay EUR {gaps[0]:.0f} less (next day versus same day) and EUR {gaps[1]:.0f} less (within 3 days versus next day)")
        print(f"    standard deviation across weeks {sd(worlds):.3f}, across days within a week {sd(days):.3f}, delivery site {sd(to):.3f}, pickup site {sd(frm):.3f}")
        print("    delivery site (log price):", ", ".join(f"{k} {v:+.3f}" for k, v in sorted(to.items(), key=lambda x: x[1])))
        print("    pickup site  (log price):", ", ".join(f"{k} {v:+.3f}" for k, v in sorted(frm.items(), key=lambda x: x[1])))
        print("    level by week:", ", ".join(f"x{math.exp(level + v):.2f}" for v in worlds.values()))
    return {"slope": round(float(slope), 2), "level": round(float(level), 4), "trust": round(float(w[columns["trust"]] / slope), 4), "gaps": list(gaps),
            "sd": {"world": round(sd(worlds), 3), "day": round(sd(days), 3), "to": round(sd(to), 3), "from": round(sd(frm), 3)},
            "places": {"to": {k: round(float(v), 3) for k, v in to.items()}, "from": {k: round(float(v), 3) for k, v in frm.items()}}}


def menus(rows: list) -> None:
    """Compare the dealer's choice against the price gap between two quoted options."""
    pairs = [r for r in rows if len(r["offered"]) >= 2 and r["won"]]
    picks = Counter()
    for r in pairs:
        order = [k for k in r["kinds"] if k in r["offered"]]
        cheapest = min(order, key=lambda k: r["offered"][k] * r["lists"][k])
        picks[("fastest" if r["option"] == order[0] else "slower", "cheapest" if r["option"] == cheapest else "more expensive")] += 1
    print(f"\n  Option choices ({len(pairs)} wins with >= 2 options): {dict(picks)}")


def learner_score(runs: list, world_map: dict, settings: dict) -> float:
    """Run the bot's price learner (dispatch.Desk) through saved weeks in chronological order.
    Score the prediction before each dealer reply with log loss. Lower is better. Runs offline."""
    import dispatch
    knobs = {name: value for name, value in settings.items() if not name.startswith("_")}
    saved = {name: getattr(dispatch.P, name) for name in knobs}
    for name, value in knobs.items():
        setattr(dispatch.P, name, value)
    total, n = 0.0, 0
    for run in runs:
        desk = dispatch.Desk.__new__(dispatch.Desk)
        desk.model, desk.beliefs, desk.quoted, desk.trust, desk.requests, desk.journal, desk.down = settings.get("_model", {}), {}, {}, {}, {}, None, {}
        desk.atlas = Atlas(world_map, run["roster"])
        events = []
        for r in run["reveal"]["requests"]:
            events.append((r["request"]["respondBy"], 1, r))
        late = {e["line"]["orderId"] for e in run["events"] if e["kind"] == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId")}
        dealer_of = {e["order"]["id"]: e["order"]["dealerId"] for e in run["events"] if e["kind"] == "order_won"}
        for e in run["events"]:
            if e["kind"] == "delivered" and e["orderId"] in dealer_of:
                events.append((e["at"], 0, (dealer_of[e["orderId"]], e["orderId"] not in late)))
        for _, kind, item in sorted(events, key=lambda x: (x[0], x[1])):
            if kind == 0:
                dealer, on_time = item
                desk.trust[dealer] = min(25, desk.trust.get(dealer, 0) + 1) if on_time else desk.trust.get(dealer, 0) // 2
                continue
            request, quote = item["request"], item.get("quote")
            if not quote or len(request["legs"]) != 1:
                continue
            lists = {o["kind"]: o["listPriceCents"] for o in request["options"]}
            offered = {k: p / lists[k] for k, p in quote.items() if p / lists[k] < 3.5}
            if not offered:
                continue
            desk.requests[request["id"]] = request
            won = item["outcome"] == "won"
            if len(offered) == 1:  # only these are scored: we know which option the dealer weighed
                (k, m), = offered.items()
                index, down = [o["kind"] for o in request["options"]].index(k), desk.down_chance(request)
                p = (1 - down) * desk.chance(request, index, m) + down * desk.alone(request, index, m)
                p = min(1 - 1e-6, max(1e-6, p))
                total -= math.log(p if won else 1 - p)
                n += 1
            desk.quoted[request["id"]] = offered
            desk.learn(request["id"], item.get("option") if won else None)
    for name, value in saved.items():
        setattr(dispatch.P, name, value)
    return total / max(1, n)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="only read files whose names contain this string")
    parser.add_argument("--runs", default="runs", help="directory containing the saved weeks")
    parser.add_argument("--map", default="map.json")
    parser.add_argument("--out", default="model.json")
    args = parser.parse_args()
    world_map = json.load(open(args.map, encoding="utf-8"))
    runs = []
    for path in sorted(glob.glob(os.path.join(args.runs, "L8_*.json.gz"))):
        if args.only in path:
            run = load(path)
            if run.get("reveal") and run.get("roster"):
                runs.append(run)
    measured = [r for r in runs if r["params"].get("explore")]  # exploration weeks with randomized prices and fees
    print(f"{len(runs)} saved weeks, including {len(measured)} exploration weeks")
    own = [r for r in runs if r["params"].get("try_fees")]  # weeks played normally with randomized opening fees
    fleet_runs = own or measured or runs  # the fee of a gig is judged as the bot plays it: a gig that waits goes up fee steps
    print(f"Driver model fitted on {len(fleet_runs)} weeks" + (" played normally with randomized opening fees (try_fees)" if own else ""))
    rows = []
    for run in fleet_runs:
        table = orders_table(run, Atlas(world_map, run["roster"]))
        rows += table
        print(f"{run['path'][-60:]:<62}{len(table):>4} orders  {sum(r['on_time'] for r in table) / max(1, len(table)):6.1%} on time", flush=True)
    weights = fit_on_time(rows, ON_TIME_SIGNS)
    calibration(rows, weights, lambda r: round(r["fee"], 2), "by fee (x typical)")
    calibration(rows, weights, lambda r: "<5h" if r["slack_h"] < 5 else "5-8h" if r["slack_h"] < 8 else "8-12h" if r["slack_h"] < 12 else "12-24h" if r["slack_h"] < 24 else "24-48h" if r["slack_h"] < 48 else ">=48h", "by slack hours")
    calibration(rows, weights, lambda r: "0-3" if r["near"] < 4 else "4-20" if r["near"] < 21 else "21-100" if r["near"] < 101 else ">100", "by driver count near pickup")
    calibration(rows, weights, lambda r: "<40" if r["km"] < 40 else "40-100" if r["km"] < 100 else "100-200" if r["km"] < 200 else "200-400" if r["km"] < 400 else ">=400", "by lane length in km")
    for fee in FEES:
        for label, pick in (("<8h", lambda r: r["slack_h"] < 8), ("8-24h", lambda r: 8 <= r["slack_h"] < 24), (">=24h", lambda r: r["slack_h"] >= 24)):
            some = [r for r in rows if r["fee"] == fee and pick(r)]
            if some:
                print(f"    fee {fee:<5} slack hours {label:<6} n {len(some):>4}  on time {sum(r['on_time'] for r in some) / len(some):6.1%}  booked before warning {sum(r['booked'] for r in some) / len(some):6.1%}")
    late_rows, booked_rows = [r for r in rows if not r["on_time"]], [r for r in rows if r["booked"]]
    unbooked = [r for r in rows if not r["booked"]]
    model = {"on_time": weights, "on_time_orders": len(rows), "on_time_weeks": len(fleet_runs),
             "refund": round(sum(r["refund"] for r in late_rows) / max(1, sum(r["list"] for r in late_rows)), 3),
             "booked_late": round(sum(not r["on_time"] for r in booked_rows) / max(1, len(booked_rows)), 3),
             "unbooked_late": round(sum(not r["on_time"] for r in unbooked) / max(1, len(unbooked)), 3)}
    if own:
        model["paid"] = fit_paid(rows)
    print(f"\nAverage refund for a late order is {model['refund']:.2f} x list price ({len(late_rows)} late orders)")
    print(f"Booked before warning: {len(booked_rows)} orders, late {model['booked_late']:.1%}. Unbooked: {len(unbooked)} orders, late {sum(not r['on_time'] for r in unbooked) / max(1, len(unbooked)):.1%}")

    market_runs = measured or runs
    quotes = [row for run in market_runs for row in quotes_table(run)]
    market = fit_market(quotes)
    menus(quotes)
    model["market"], model["market_quotes"], model["places"] = {k: v for k, v in market.items() if k != "places"}, len(quotes), market["places"]
    json.dump(model, open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"\nWrote {args.out}")

    # Tune the price learner's slope and component spreads on the first half of the weeks. Use the second half only for evaluation.
    tune, hold = market_runs[:len(market_runs) // 2], market_runs[len(market_runs) // 2:]
    places_tune = fit_market([row for run in tune for row in quotes_table(run)], quiet=True, gaps=tuple(market["gaps"]))["places"]
    knobs = dict(level0=math.exp(market["level"]), slope=market["slope"], gap_next=market["gaps"][0], gap_later=market["gaps"][1], trust=market["trust"],
                 sd_world=0.10, sd_day=0.10, sd_dealer=0.05, sd_to=0.05, sd_from=0.03, sd_lane=0.0)
    with_table = {"_model": {"places": places_tune}}
    print("\nBOT PRICE LEARNER log loss (lower is better):")
    print(f"    before tuning: tune {learner_score(tune, world_map, {**knobs, **with_table}):.4f}  hold {learner_score(hold, world_map, {**knobs, **with_table}):.4f}  (without location tables: hold {learner_score(hold, world_map, {**knobs, '_model': {}}):.4f})")
    grid = {"slope": (10.0, 12.0, 14.0, 16.0), "sd_world": (0.06, 0.10, 0.15), "sd_day": (0.10, 0.15, 0.20), "sd_dealer": (0.01, 0.02, 0.05), "sd_to": (0.03, 0.05),
            "sd_from": (0.01, 0.02, 0.04), "sd_lane": (0.0, 0.03, 0.05, 0.08)}
    for _ in range(2):  # two passes, one setting at a time
        for name, values in grid.items():
            scores = {v: learner_score(tune, world_map, {**knobs, **with_table, name: v}) for v in values}
            knobs[name] = min(scores, key=scores.get)
    print(f"    after tuning:   tune {learner_score(tune, world_map, {**knobs, **with_table}):.4f}  hold {learner_score(hold, world_map, {**knobs, **with_table}):.4f}")
    print("    selected:", {k: knobs[k] for k in grid})
    model["learner"] = {k: knobs[k] for k in grid}
    model["learner"]["slope"] = PLAYED_SLOPE
    print(f"    slope used in play: {PLAYED_SLOPE} (chosen for profit in practice)")
    json.dump(model, open(args.out, "w", encoding="utf-8"), indent=1)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
