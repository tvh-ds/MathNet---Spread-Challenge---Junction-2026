"""After a final or test final, count requests quoted in time and measure network latency.

    python check_final.py
"""
import collections
import gzip
import json
import os
import time

from spread.client import Client

client = Client()
times = []
for _ in range(6):
    start = time.time()
    final = client.final()
    times.append(time.time() - start)
print(f"Call latency (seconds): first call {times[0]:.2f}, average of subsequent calls {sum(times[1:]) / 5:.2f}")
world = client.world(final["worldId"])
print("World", world.id, "| score:", world.score())
try:
    reveal = world.reveal()
except Exception as error:
    raise SystemExit(f"Reveal unavailable (the practice session may still be running): {error}")
events = world.events()
outcomes = collections.Counter(r["outcome"] for r in reveal["requests"])
declined = sum(1 for r in reveal["requests"] if r["quote"] and min(v / next(o["listPriceCents"] for o in r["request"]["options"] if o["kind"] == k) for k, v in r["quote"].items()) > 3)
print(f"Requests: {len(reveal['requests'])} | won {outcomes['won']} | lost {outcomes['lost']} (including declines {declined}) | MISSED QUOTES {outcomes['unquoted']}")
by_day = collections.defaultdict(collections.Counter)
for r in reveal["requests"]:
    by_day[r["request"]["arrivedAt"] // 1440][r["outcome"]] += 1
for day, c in sorted(by_day.items()):
    print(f"  day {day}: won {c['won']}, lost {c['lost']}, missed {c['unquoted']}")
os.makedirs("runs", exist_ok=True)
path = os.path.join("runs", f"final_{world.id}.json.gz")
with gzip.open(path, "wt", encoding="utf-8") as out:
    json.dump({"seed": "final", "level": 8, "params": {}, "worldId": world.id, "score": world.score(), "events": events, "roster": world.roster(), "reveal": reveal}, out)
print("Saved", path)
