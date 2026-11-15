import gzip, json, sys, collections
HOUR, DAY = 60, 1440
for path in sys.argv[1:]:
    d = json.load(gzip.open(path, "rt"))
    req = {r["request"]["id"]: r["request"] for r in d["reveal"]["requests"]}
    gigs = {g["id"]: g for g in d["snapshot"]["gigs"]}
    booked = {}
    for e in d["events"]:
        if e["kind"] == "gig_booked": booked.setdefault(e["gigId"], (e["at"], e["feeCents"]))
    late = {e["line"]["orderId"] for e in d["events"] if e["kind"] == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId")}
    first = {}
    for g in sorted(gigs.values(), key=lambda g: g["postedAt"]):
        first.setdefault(g["stops"][0]["orderId"], g)
    rows = []
    for oid, g in first.items():
        typ = req[oid]["referenceFeeCents"]
        m0 = round(g["schedule"][0]["feeCents"] / typ, 2)
        b = booked.get(g["id"])
        rows.append(dict(oid=oid, m0=m0, steps=len(g["schedule"]), posted=g["postedAt"], wait=None if b is None else (b[0] - g["postedAt"]) / HOUR,
                         mb=None if b is None else round(b[1] / typ, 2), late=oid in late, day=g["postedAt"] // DAY, status=g["status"]))
    print("===", path[-50:], "score", d["score"]["marginCents"] / 100, "orders", d["score"]["wonOrders"], "on time", round(d["score"]["onTimeShare"], 3))
    print(" first gigs:", len(rows), " statuses:", dict(collections.Counter(g["status"] for g in gigs.values())), " all gigs:", len(gigs))
    by = collections.defaultdict(list)
    for r in rows: by[r["m0"]].append(r)
    for m0 in sorted(by):
        rs = by[m0]; n = len(rs)
        w = sorted(r["wait"] for r in rs if r["wait"] is not None)
        at_first = sum(1 for r in rs if r["mb"] is not None and abs(r["mb"] - m0) < 0.02)
        print(f"  opening fee x{m0:<5} n {n:>4}  booked at opening fee {at_first/n:5.0%}  within 15 min {sum(1 for x in w if x <= 0.25)/n:5.0%}  within 6h {sum(1 for x in w if x <= 6)/n:5.0%}  first gig never booked {sum(1 for r in rs if r['wait'] is None)/n:5.0%}  late {sum(r['late'] for r in rs)/n:5.1%}")
    paid = collections.Counter(r["mb"] for r in rows if r["mb"] is not None)
    print("  fee at booking (first gig):", dict(sorted(paid.items())))
    for day in range(5):
        rs = [r for r in rows if r["day"] == day and r["m0"] <= 0.86]
        if rs: print(f"  day {day}: gigs opening at 0.85: {len(rs):>3}, booked within 15 min {sum(1 for r in rs if r['wait'] is not None and r['wait'] <= 0.25)/len(rs):5.0%}, booked at 0.85 {sum(1 for r in rs if r['mb'] is not None and r['mb'] <= 0.86)/len(rs):5.0%}")
