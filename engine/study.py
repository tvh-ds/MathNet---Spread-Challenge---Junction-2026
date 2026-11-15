"""Mot tuan da luu cua bot v4: tien di dau, theo loai xe, theo ngay, ghep xe, va gia cua don tre trong tuan."""
import gzip, json, sys, collections, math
from world import Atlas, DAY, HOUR

def study(path, wm, brief=False):
    d = json.load(gzip.open(path, "rt"))
    atlas = Atlas(wm, d["roster"])
    req = {r["request"]["id"]: r for r in d["reveal"]["requests"]}
    ev = d["events"]
    gigs = {g["id"]: g for g in (d.get("snapshot") or {}).get("gigs", [])}
    gig_orders = {gid: list(dict.fromkeys(s["orderId"] for s in g["stops"])) for gid, g in gigs.items()}
    won = {e["order"]["id"]: (e["at"], e["order"]) for e in ev if e["kind"] == "order_won"}
    cancelled = {e["orderId"] for e in ev if e["kind"] == "order_cancelled"}
    led = collections.Counter(); per = collections.defaultdict(collections.Counter)
    for e in ev:
        if e["kind"] != "ledger": continue
        l = e["line"]; led[l["kind"]] += l["cents"]
        owners = [l["orderId"]] if l.get("orderId") else gig_orders.get(l.get("gigId"), [])
        if l["kind"] == "driver_fee" and l.get("gigId") in gig_orders and len(gig_orders[l["gigId"]]) > 1:
            owners = gig_orders[l["gigId"]]
            total = sum(req[o]["request"]["referenceFeeCents"] for o in owners)
            for o in owners: per[o]["driver_fee"] += l["cents"] * req[o]["request"]["referenceFeeCents"] / total
            for o in owners: per[o]["paired"] = 1
            continue
        for o in owners[:1]: per[o][l["kind"]] += l["cents"]
    s = d["score"]
    rows = []
    for oid, (at, o) in won.items():
        if oid in cancelled or len(o["legs"]) != 1: continue
        r = req[oid]["request"]; leg = r["legs"][0]
        lst = next(x["listPriceCents"] for x in r["options"] if x["kind"] == o["option"])
        km = atlas.km[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])]
        slack = (o["lastPickupAt"] - at) / HOUR
        late = per[oid]["late_refund"] < 0 or per[oid]["undelivered_penalty"] < 0
        rows.append(dict(oid=oid, day=at // DAY, mult=o["priceCents"] / lst, price=o["priceCents"], typ=r["referenceFeeCents"], fee=-per[oid]["driver_fee"], opened=(d.get("opened") or {}).get(oid),
                         net=sum(v for k, v in per[oid].items() if k != "paired"), late=late, km=km, slack=slack, paired=bool(per[oid]["paired"]), option=o["option"], dealer=o["dealerId"], lst=lst))
    n = len(rows)
    print(f"=== {path[-52:]}: EUR {s['marginCents']/100:,.0f}, {s['wonOrders']} orders, {s['onTimeShare']:.1%} on time; per order EUR {s['marginCents']/100/max(1,s['wonOrders']):.1f}")
    print("  ledger EUR:", ", ".join(f"{k} {v/100:,.0f}" for k, v in sorted(led.items(), key=lambda x: -abs(x[1]))))
    tot_list = sum(r["lst"] for r in rows); tot_typ = sum(r["typ"] for r in rows)
    print(f"  price x{sum(r['price'] for r in rows)/tot_list:.3f} list; fee paid x{sum(r['fee'] for r in rows)/tot_typ:.3f} typical; typical/list {tot_typ/tot_list:.2f}; avg list EUR {tot_list/n/100:.1f}; quoted {sum(1 for r in req.values() if r.get('quote') and max(p / next(o['listPriceCents'] for o in r['request']['options'] if o['kind']==k) for k,p in r['quote'].items()) < 3.5)} of {len(req)} requests")
    if brief: return rows
    def table(label, key, order=None):
        groups = collections.defaultdict(list)
        for r in rows: groups[key(r)].append(r)
        print(f"  {label}")
        for g in (order or sorted(groups, key=str)):
            v = groups.get(g)
            if not v: continue
            print(f"    {str(g):<12} n {len(v):>4}  net/order {sum(r['net'] for r in v)/len(v)/100:6.1f}  price x{sum(r['price'] for r in v)/sum(r['lst'] for r in v):.2f}  fee x{sum(r['fee'] for r in v)/sum(r['typ'] for r in v):.2f}  late {sum(r['late'] for r in v)/len(v):5.1%}  total EUR {sum(r['net'] for r in v)/100:7,.0f}")
    table("by day", lambda r: r["day"])
    table("by km", lambda r: "<40" if r["km"] < 40 else "40-100" if r["km"] < 100 else "100-200" if r["km"] < 200 else "200-400" if r["km"] < 400 else ">=400", ["<40", "40-100", "100-200", "200-400", ">=400"])
    table("by hours left at the win", lambda r: "<8h" if r["slack"] < 8 else "8-24h" if r["slack"] < 24 else "24-48h" if r["slack"] < 48 else ">=48h", ["<8h", "8-24h", "24-48h", ">=48h"])
    table("by option", lambda r: r["option"])
    table("by fee the gig opened at", lambda r: r["opened"] if r["opened"] is not None else "?")
    table("in a two-car gig", lambda r: r["paired"])
    top = collections.Counter(r["dealer"] for r in rows).most_common(3)
    for dealer, _ in top:
        print(f"    {dealer}: " + "  ".join(f"d{day}: {sum(1 for r in rows if r['dealer']==dealer and r['day']==day)}@x{(sum(r['price'] for r in rows if r['dealer']==dealer and r['day']==day)/max(1,sum(r['lst'] for r in rows if r['dealer']==dealer and r['day']==day))):.2f}" for day in range(5)))
    two = [g for g in gigs.values() if len({s["orderId"] for s in g["stops"]}) > 1]
    print(f"  two-car gigs posted {len(two)}: " + str(dict(collections.Counter(g["status"] for g in two))) + f"; cars delivered in one: {sum(r['paired'] for r in rows)}")
    tr = d.get("trace") or []
    if tr: print("  trace (day hour: late price EUR, world shift, waiting, won, late expected):", "  ".join(f"d{t[0]//DAY} {t[0]%DAY//60}h: {t[1]},{t[2]:+.2f},{t[3]},{t[4]},{t[5]}" for t in tr[::6]))
    return rows

if __name__ == "__main__":
    wm = json.load(open("map.json"))
    for p in sys.argv[1:]:
        study(p, wm)
