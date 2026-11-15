"""Chay lai cac su kien cua mot tuan da luu qua ban Desk moi, voi mot the gioi gia: de bat loi truoc khi dung may chu that.
Khong do duoc diem (don thang la cua chinh sach cu), chi kiem tra desk khong vo va cac quyet dinh trong hop ly."""
import gzip, json, sys, collections, statistics, time
import dispatch
from dispatch import Desk, P

class FakeClient:
    def __init__(self, world_map): self._map = world_map
    def map(self): return self._map
    def worlds(self): return []

class FakeWorld:
    def __init__(self, run, world_map):
        self.id, self.client, self._roster, self.n, self.log = run["worldId"], FakeClient(world_map), run["roster"], 0, []
    def roster(self): return self._roster
    def act(self, actions):
        results = []
        for a in actions:
            self.log.append(a)
            if a["type"] == "post":
                self.n += 1
                results.append({"ok": True, "id": f"f{self.n}"})
            else:
                results.append({"ok": True})
        return results

def replay(path, params=None):
    for k, v in (params or {}).items(): setattr(P, k, v)
    run = json.load(gzip.open(path, "rt"))
    world = FakeWorld(run, json.load(open("map.json")))
    desk = Desk(world, 8, 0)
    gig_order = {}
    for g in (run.get("snapshot") or {}).get("gigs", []): gig_order[g["id"]] = g["stops"][0]["orderId"]
    for e in run["events"]:
        if e["kind"] in ("picked_up", "delivered", "visit_failed"): gig_order.setdefault(e["gigId"], e["orderId"])
    stats = collections.Counter(); trail = []
    t0 = time.time()
    for e in run["events"]:
        if e["kind"] in ("gig_viewed", "gig_started", "picked_up"): continue
        desk.now = max(desk.now, e["at"])
        if "gigId" in e and e["kind"] != "ledger":
            oid = gig_order.get(e["gigId"])
            fake = desk.gigs_of(oid)[0] if oid and desk.gigs_of(oid) else None
            if fake is None and e["kind"] in ("gig_booked", "gig_dropped", "no_show", "gig_expired", "visit_failed"):
                stats["skipped " + e["kind"]] += 1
                continue
            e = {**e, "gigId": fake}
        desk.handle(e)
        desk.send()
        stats[e["kind"]] += 1
        if e["kind"] == "price_request" and stats["price_request"] % 100 == 0:
            trail.append((e["at"] // 1440, round(desk.late_price / 100), round(desk.world_shift, 2), desk.queue()[0], desk.won))
    elapsed = time.time() - t0
    quotes = [a for a in world.log if a["type"] == "quote"]
    posts = [a for a in world.log if a["type"] == "post"]
    reqs = desk.requests
    mults, declined, menu = collections.defaultdict(list), 0, collections.Counter()
    for q in quotes:
        r = reqs[q["requestId"]]; lists = {o["kind"]: o["listPriceCents"] for o in r["options"]}
        ms = {k: p / lists[k] for k, p in q["prices"].items()}
        if max(ms.values()) >= 3.9: declined += 1; continue
        menu[len(ms)] += 1
        for k, m in ms.items(): mults[k].append(m)
    fee0 = collections.Counter(); steps = collections.Counter(); windows = collections.Counter(); plates = 0; manual = 0
    for p in posts:
        oid = p["stops"][0]["orderId"]; typical = reqs[oid]["referenceFeeCents"]
        fee0[round(p["schedule"][0]["feeCents"] / typical, 2)] += 1
        steps[len(p["schedule"])] += 1
        for s in p["stops"]:
            if "window" in s: windows[s["kind"]] += 1
        plates += any(s.get("withPlates") for s in p["stops"]); manual += p["audience"]["manualLicence"]
    print(f"=== {path[-60:]}  ({elapsed:.1f}s, {elapsed / max(1, stats['price_request']) * 1000:.1f} ms moi request)")
    print("  su kien:", dict(stats))
    print(f"  bao gia {len(quotes)}, tu choi {declined}, so option moi bao gia {dict(menu)}")
    for k, v in mults.items():
        v.sort(); print(f"    {k:<14} n {len(v):>4}  boi so list: 10% {v[len(v)//10]:.2f}  trung vi {v[len(v)//2]:.2f}  90% {v[len(v)*9//10]:.2f}")
    print(f"  gig dang {len(posts)}: phi mo dau {dict(sorted(fee0.items()))}; so bac {dict(steps)}; cua so rieng {dict(windows)}; bien so {plates}, so san {manual}")
    print("  (ngay, gia cua mot don tre EUR, do lech the gioi, hang doi, don thang):", trail)
    print(f"  trust: {dict(sorted(desk.trust.items(), key=lambda x: -x[1])[:6])}  beliefs world: {tuple(round(x, 3) for x in desk.beliefs.get(('world',), (0, 0)))}")
    return desk, world

if __name__ == "__main__":
    for path in sys.argv[1:]:
        replay(path)
