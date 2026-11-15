"""Sau khi mot buoi (test) final ket thuc: xem bot da bao gia kip bao nhieu yeu cau, va do do tre mang.

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
print(f"Do tre moi luot goi (giay): lan dau {times[0]:.2f}, cac lan sau trung binh {sum(times[1:]) / 5:.2f}")
world = client.world(final["worldId"])
print("World", world.id, "| diem:", world.score())
try:
    reveal = world.reveal()
except Exception as error:
    raise SystemExit(f"Chua xem duoc reveal (buoi tap chua ket thuc?): {error}")
events = world.events()
outcomes = collections.Counter(r["outcome"] for r in reveal["requests"])
declined = sum(1 for r in reveal["requests"] if r["quote"] and min(v / next(o["listPriceCents"] for o in r["request"]["options"] if o["kind"] == k) for k, v in r["quote"].items()) > 3)
print(f"Yeu cau: {len(reveal['requests'])} | thang {outcomes['won']} | thua {outcomes['lost']} (trong do minh tu choi {declined}) | KHONG KIP BAO GIA {outcomes['unquoted']}")
by_day = collections.defaultdict(collections.Counter)
for r in reveal["requests"]:
    by_day[r["request"]["arrivedAt"] // 1440][r["outcome"]] += 1
for day, c in sorted(by_day.items()):
    print(f"  ngay {day}: thang {c['won']}, thua {c['lost']}, khong kip {c['unquoted']}")
os.makedirs("runs", exist_ok=True)
path = os.path.join("runs", f"final_{world.id}.json.gz")
with gzip.open(path, "wt", encoding="utf-8") as out:
    json.dump({"seed": "final", "level": 8, "params": {}, "worldId": world.id, "score": world.score(), "events": events, "roster": world.roster(), "reveal": reveal}, out)
print("Da luu", path)
