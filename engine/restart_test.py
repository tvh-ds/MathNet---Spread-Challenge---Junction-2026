"""Test restart recovery. Play half a week in a mock world, stop, and rebuild the desk from the snapshot, history, and journal.
Compare the new and old desks on price learning, trust, orders, and gigs."""
import gzip, json, os, shutil, sys
import dispatch, replay_test
from dispatch import Desk

def run(path, stop_at):
    dispatch.LIVE = True
    shutil.rmtree(os.path.join(dispatch.HERE, "journal"), ignore_errors=True)
    data = json.load(gzip.open(path, "rt"))
    world = replay_test.FakeWorld(data, json.load(open("map.json")))
    desk = Desk(world, 8, 0)
    gig_order = {}
    for e in data["events"]:
        if e["kind"] in ("picked_up", "delivered", "visit_failed"): gig_order.setdefault(e["gigId"], e["orderId"])
    history, orders, posted_at, answered = [], {}, {}, set()
    for e in data["events"]:
        if e["at"] > stop_at: break
        if e["kind"] in ("gig_viewed", "gig_started", "picked_up"): continue
        desk.now = max(desk.now, e["at"])
        if "gigId" in e and e["kind"] != "ledger":
            oid = gig_order.get(e["gigId"]); fake = desk.gigs_of(oid)[0] if oid and desk.gigs_of(oid) else None
            if fake is None and e["kind"] in ("gig_booked", "gig_dropped", "no_show", "gig_expired", "visit_failed"): continue
            e = {**e, "gigId": fake}
        history.append(e)
        if e["kind"] == "order_won": orders[e["order"]["id"]] = json.loads(json.dumps(e["order"])); answered.add(e["order"]["id"])
        if e["kind"] == "order_lost": answered.add(e["requestId"])
        if e["kind"] == "order_changed" and e["order"]["id"] in orders: orders[e["order"]["id"]] = json.loads(json.dumps(e["order"]))
        if e["kind"] == "order_cancelled" and e["orderId"] in orders: orders[e["orderId"]]["status"] = "cancelled"
        if e["kind"] == "delivered" and e["orderId"] in orders:
            orders[e["orderId"]]["deliveredAt"][e["leg"]] = e["at"]
            if all(x is not None for x in orders[e["orderId"]]["deliveredAt"]): orders[e["orderId"]]["status"] = "delivered"
        before = len(world.log)
        desk.handle(e); desk.send()
        for a in world.log[before:]:
            if a["type"] == "post": posted_at[f"f{sum(1 for x in world.log[:world.log.index(a) + 1] if x['type'] == 'post')}"] = desk.now
    gigs = []
    for gig_id, action in desk.posts.items():
        oid = action["stops"][0]["orderId"]
        live = any(desk.leg_gigs.get(s["orderId"], {}).get(s["leg"]) == gig_id for s in action["stops"])
        done = all(orders.get(s["orderId"], {}).get("status") == "delivered" for s in action["stops"])  # a two-car gig works until its last car is there
        status = "done" if done else "booked" if gig_id in desk.booked and live else "open" if live else "withdrawn"
        gigs.append({"id": gig_id, "status": status, "stops": action["stops"], "audience": action["audience"], "schedule": action["schedule"], "postedAt": posted_at.get(gig_id, 0)})
    open_requests = [e["request"] for e in history if e["kind"] == "price_request" and e["request"]["id"] not in answered and e["request"]["respondBy"] > desk.now]
    snapshot = {"now": desk.now, "endsAt": 10 ** 9, "gigs": gigs, "orders": list(orders.values()), "openRequests": open_requests}
    desk2 = Desk(world, 8, desk.now)
    before = len(world.log)
    desk2.rejoin(snapshot, history); desk2.send()
    after = world.log[before:]
    same_beliefs = all(abs(desk.beliefs[k][0] - desk2.beliefs.get(k, (9, 9))[0]) < 1e-9 and abs(desk.beliefs[k][1] - desk2.beliefs.get(k, (9, 9))[1]) < 1e-9 for k in desk.beliefs) and len(desk.beliefs) == len(desk2.beliefs)
    live_orders = {o for o in desk.orders}
    print(f"stop at minute {stop_at} (day {stop_at // 1440}): history {len(history)} events, {len(orders)} orders, {len(gigs)} gigs, {len(open_requests)} open requests")
    print("  beliefs equal:", same_beliefs, f"({len(desk.beliefs)} parts)", "max diff", max(abs(desk.beliefs[k][0] - desk2.beliefs.get(k, (9, 9))[0]) for k in desk.beliefs), "missing", [k for k in desk.beliefs if k not in desk2.beliefs][:3])
    print("  trust equal:", desk.trust == desk2.trust, dict(sorted(desk.trust.items(), key=lambda x: -x[1])[:4]))
    print("  won equal:", desk.won, desk2.won, "| orders known:", len(desk.orders), len(desk2.orders))
    print("  ended equal:", desk.ended == desk2.ended, len(desk.ended))
    print("  forecast equal:", desk.forecast == {k: v for k, v in desk2.forecast.items()}, len(desk.forecast), len(desk2.forecast))
    waiting1 = sorted(o for o in desk.orders if desk.waits(o)); waiting2 = sorted(o for o in desk2.orders if desk2.waits(o))
    print("  waiting orders equal:", waiting1 == waiting2, len(waiting1), len(waiting2))
    diff = [o for o in waiting1 if o in waiting2 and abs(desk.shown(o) - desk2.shown(o)) >= 0.02]
    print("  shown fees equal:", not diff, "| differ:", len(diff), "of which urgent (the fake snapshot keeps the first schedule):", sum(1 for o in diff if o in desk.urgent))
    worst = max((abs(desk.beliefs[k][0] - desk2.beliefs.get(k, (9, 9))[0]) for k in desk.beliefs), default=0)
    print("  largest gap between beliefs:", worst)
    desk.seen_at = desk2.seen_at = -1; desk.look(); desk2.look()
    print(f"  late price: {desk.late_price / 100:.1f} vs {desk2.late_price / 100:.1f}; world shift {desk.world_shift:.3f} vs {desk2.world_shift:.3f}")
    print("  actions after the restart:", {t: sum(1 for a in after if a["type"] == t) for t in {a["type"] for a in after}})
    dispatch.LIVE = False

if __name__ == "__main__":
    for stop in (2 * 1440 + 700, 3 * 1440 + 900):
        run(sys.argv[1], stop)
