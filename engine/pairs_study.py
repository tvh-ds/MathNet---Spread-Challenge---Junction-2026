"""Which two-car gigs found a driver, on saved weeks:  python pairs_study.py runs/L8_halal-*v44*.json.gz
A table per sign (way back, driving time, fee, hour, weekday, drivers nearby), and what the cars cost alone or together."""
import collections
import gzip
import json
import sys

from world import DAY, HOUR, Atlas, crow_km

world_map = json.load(open("map.json", encoding="utf-8"))
rows, cars = [], collections.Counter()
for path in sys.argv[1:]:
    run = json.load(gzip.open(path, "rt", encoding="utf-8"))
    if not run.get("reveal") or not run.get("snapshot"):
        continue
    atlas = Atlas(world_map, run["roster"])
    requests = {r["request"]["id"]: r["request"] for r in run["reveal"]["requests"]}
    booked_at, paid = {}, collections.Counter()
    late = {e["line"]["orderId"] for e in run["events"] if e["kind"] == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId")}
    for e in run["events"]:
        if e["kind"] == "gig_booked":
            booked_at.setdefault(e["gigId"], e["at"])
        elif e["kind"] == "ledger" and e["line"]["kind"] == "driver_fee" and e["line"].get("gigId"):
            paid[e["line"]["gigId"]] -= e["line"]["cents"]
    for gig in run["snapshot"]["gigs"]:
        ids = list(dict.fromkeys(s["orderId"] for s in gig["stops"]))
        if not all(i in requests and len(requests[i]["legs"]) == 1 for i in ids):
            continue
        typical = sum(requests[i]["referenceFeeCents"] for i in ids)
        if paid[gig["id"]]:
            key = "two cars" if len(ids) > 1 else "one car"
            cars[key, "cars"] += len(ids); cars[key, "paid"] += paid[gig["id"]]; cars[key, "typical"] += typical; cars[key, "late"] += sum(i in late for i in ids)
        if len(ids) != 2:
            continue
        x, y = requests[ids[0]]["legs"][0], requests[ids[1]]["legs"][0]
        a, b, c, d = x["pickup"]["placeId"], x["delivery"]["placeId"], y["pickup"]["placeId"], y["delivery"]["placeId"]
        hop = atlas.minutes[(b, c)] if b != c else 0
        rows.append(dict(booked=gig["id"] in booked_at, wait=booked_at.get(gig["id"], 10 ** 9) - gig["postedAt"], back=crow_km(atlas.spot[d], atlas.spot[a]),
                         hours=(atlas.drive(x) + hop + atlas.drive(y)) / HOUR, fee=gig["schedule"][0]["feeCents"] / 100, multiple=gig["schedule"][0]["feeCents"] / typical,
                         near=atlas.near[a], near_end=atlas.near[d], hour=gig["postedAt"] % DAY // HOUR, weekday=gig["postedAt"] // DAY % 7, same=b == c))
print(f"{len(rows)} two-car gigs, {sum(r['booked'] for r in rows)} found a driver = {sum(r['booked'] for r in rows) / max(1, len(rows)):.0%}")
for key in ("one car", "two cars"):
    if cars[key, "cars"]:
        print(f"  {key:<9} {cars[key, 'cars']:>6} cars  fee x{cars[key, 'paid'] / cars[key, 'typical']:.3f} typical  late {cars[key, 'late'] / cars[key, 'cars']:.1%}")


def table(label, key, order):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    print(label)
    for k in order:
        v = groups.get(k, [])
        if v:
            quick = sum(r["booked"] and r["wait"] <= 15 for r in v)
            print(f"   {str(k):<12} n {len(v):>5}  found a driver {sum(r['booked'] for r in v) / len(v):5.0%}  within 15 min {quick / len(v):5.0%}  fee x{sum(r['multiple'] for r in v) / len(v):.2f}  EUR {sum(r['fee'] for r in v) / len(v):4.0f}")


table("by the way back from the last delivery to the first pickup (km)", lambda r: "<30" if r["back"] < 30 else "30-100" if r["back"] < 100 else "100-200" if r["back"] < 200 else "200-300" if r["back"] < 300 else ">=300", ["<30", "30-100", "100-200", "200-300", ">=300"])
table("by planned driving (hours)", lambda r: "<2" if r["hours"] < 2 else "2-3" if r["hours"] < 3 else "3-4" if r["hours"] < 4 else ">=4", ["<2", "2-3", "3-4", ">=4"])
table("by the gig's fee (EUR)", lambda r: "<50" if r["fee"] < 50 else "50-80" if r["fee"] < 80 else "80-110" if r["fee"] < 110 else ">=110", ["<50", "50-80", "80-110", ">=110"])
table("by its multiple of the two typical fees", lambda r: round(r["multiple"], 2), sorted({round(r["multiple"], 2) for r in rows}))
table("by drivers living within 30 km of the first pickup", lambda r: "0-3" if r["near"] < 4 else "4-20" if r["near"] < 21 else "21-100" if r["near"] < 101 else ">100", ["0-3", "4-20", "21-100", ">100"])
table("by drivers living within 30 km of the last delivery", lambda r: "0-3" if r["near_end"] < 4 else "4-20" if r["near_end"] < 21 else "21-100" if r["near_end"] < 101 else ">100", ["0-3", "4-20", "21-100", ">100"])
table("by weekday", lambda r: r["weekday"], range(7))
table("by hour", lambda r: r["hour"] // 2 * 2, range(0, 24, 2))
table("second car starts where the first ends", lambda r: r["same"], [True, False])
