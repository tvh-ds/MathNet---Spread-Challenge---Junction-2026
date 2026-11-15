"""Report where money went and where and why orders were late, using files in runs/."""
import gzip, json, sys, collections, glob
HOUR, DAY = 60, 1440
METRO = {"helsinki", "espoo", "vantaa"}

def load(path):
    return json.load(gzip.open(path, "rt", encoding="utf-8"))

def table(d):
    ev, rv = d["events"], d["reveal"]
    req = {r["request"]["id"]: r for r in rv["requests"]}
    homes = collections.Counter(x["homePlaceId"] for x in d["roster"])
    def near(p): return sum(homes[t] for t in METRO) if p in METRO else homes[p]
    orders, gig_orders, booked_at, fee_of, won_at = {}, collections.defaultdict(set), {}, {}, {}
    warned, failed, dropped_g, cancelled = {}, collections.Counter(), collections.Counter(), set()
    ledger = collections.Counter(); per = collections.defaultdict(collections.Counter)
    for e in ev:
        k = e["kind"]
        if k == "order_won": orders[e["order"]["id"]] = e["order"]; won_at[e["order"]["id"]] = e["at"]
        elif k == "order_cancelled": cancelled.add(e["orderId"])
        elif k in ("picked_up", "delivered", "visit_failed"): gig_orders[e["gigId"]].add(e["orderId"])
        if k == "visit_failed": failed[e["orderId"]] += 1; per[e["orderId"]]["fail_" + e["reason"]] += 1
        if k == "deadline_close": warned.setdefault(e["orderId"], e["at"])
        if k == "gig_booked": booked_at[e["gigId"]] = e["at"]; fee_of[e["gigId"]] = e["feeCents"]
        if k == "gig_dropped": dropped_g[e["gigId"]] += 1
        if k == "ledger":
            l = e["line"]; ledger[l["kind"]] += l["cents"]
            oid = l.get("orderId")
            if not oid and l.get("gigId"):
                os_ = gig_orders.get(l["gigId"]); oid = next(iter(os_)) if os_ else None
            if oid: per[oid][l["kind"]] += l["cents"]
    rows = []
    for oid, o in orders.items():
        if oid in cancelled: continue
        r = req[oid]["request"]; leg = r["legs"][0]
        opt = next(x for x in r["options"] if x["kind"] == o["option"])
        gigs = [g for g, s in gig_orders.items() if oid in s]
        first_book = min((booked_at[g] for g in gigs if g in booked_at), default=None)
        refund = -sum(v for k, v in per[oid].items() if "refund" in k or "penal" in k)
        rows.append(dict(id=oid, option=o["option"], price=o["priceCents"], list=opt["listPriceCents"], typical=r["referenceFeeCents"],
            mult=o["priceCents"] / opt["listPriceCents"], slack=(o["lastPickupAt"] - won_at[oid]) / HOUR,
            pickup=leg["pickup"]["placeId"], delivery=leg["delivery"]["placeId"], np=near(leg["pickup"]["placeId"]), nd=near(leg["delivery"]["placeId"]),
            note=bool(r["note"]), premium=leg["car"]["premium"], late=refund > 0, refund=refund, warned=oid in warned,
            booked_before_warn=first_book is not None and (oid not in warned or first_book < warned[oid]),
            wait=None if first_book is None else (first_book - won_at[oid]) / HOUR, failed=failed[oid],
            drops=sum(dropped_g[g] for g in gigs), net=sum(per[oid].values()), day=won_at[oid] // DAY,
            fee=-sum(v for k, v in per[oid].items() if "fee" in k and "release" not in k), kinds=dict(per[oid])))
    return ledger, rows, d

def share(rows, key, label):
    groups = collections.defaultdict(list)
    for r in rows: groups[key(r)].append(r)
    print(f"  {label}")
    for g in sorted(groups, key=str):
        rs = groups[g]; n = len(rs)
        print(f"    {str(g):<22} orders {n:>4}  late {sum(r['late'] for r in rs)/n:6.1%}  warned {sum(r['warned'] for r in rs)/n:6.1%}  profit/order {sum(r['net'] for r in rs)/n/100:7.1f}  price x{sum(r['mult'] for r in rs)/n:.2f}  fee x{sum(r['fee'] for r in rs)/max(1,sum(r['typical'] for r in rs)):.2f}")

for path in sys.argv[1:] or sorted(glob.glob("runs/*.json.gz")):
    ledger, rows, d = table(load(path))
    n = len(rows); late = [r for r in rows if r["late"]]
    print(f"\n=== {path}\n  score: {d['score']['marginCents']/100:,.0f} EUR, {n} orders, late {len(late)} ({len(late)/n:.1%})")
    print("  ledger (EUR): " + ", ".join(f"{k} {v/100:,.0f}" for k, v in sorted(ledger.items(), key=lambda x: -abs(x[1]))))
    cause = collections.Counter()
    for r in late:
        cause["no driver before warning" if not r["booked_before_warn"] else "failed pickup" if r["failed"] else "driver dropped the gig" if r["drops"] else "other (slow driving, opening hours, change of plans)"] += 1
    print("  causes of late orders:", dict(cause))
    print("  pickup failures by reason:", dict(collections.Counter(k for r in rows for k in r["kinds"] if k.startswith("fail_") for _ in range(r["kinds"][k]))))
    share(rows, lambda r: r["option"], "by option")
    share(rows, lambda r: "<5h" if r["slack"] < 5 else "5-8h" if r["slack"] < 8 else "8-12h" if r["slack"] < 12 else "12-24h" if r["slack"] < 24 else ">=24h", "by slack hours")
    share(rows, lambda r: "<6k" if r["typical"] < 6000 else "6-10k" if r["typical"] < 10000 else "10-15k" if r["typical"] < 15000 else ">=15k", "by typical fee in cents (a proxy for lane length)")
    share(rows, lambda r: "0-3" if r["np"] < 4 else "4-20" if r["np"] < 21 else "21-100" if r["np"] < 101 else ">100", "by drivers living near pickup")
    share(rows, lambda r: "0-3" if r["nd"] < 4 else "4-20" if r["nd"] < 21 else "21-100" if r["nd"] < 101 else ">100", "by drivers living near delivery")
    share(rows, lambda r: r["note"], "has a dealer note")
    share(rows, lambda r: r["day"], "by day the order was won")
    waits = sorted(r["wait"] for r in rows if r["wait"] is not None)
    print(f"  wait for a driver (hours): median {waits[len(waits)//2]:.1f}, 75% {waits[len(waits)*3//4]:.1f}, 90% {waits[len(waits)*9//10]:.1f}; never booked: {sum(r['wait'] is None for r in rows)}")
