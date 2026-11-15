"""So sanh cac bo dau hieu cua mo hinh dung han bang kiem dinh cheo theo tuan (bo han mot so tuan ra khi khop)."""
import glob, json, math, sys
import numpy as np
import fit
from world import Atlas

wm = json.load(open("map.json"))
runs = [fit.load(p) for p in sorted(glob.glob("ex/L8_*.json.gz"))]
BASE = ["one", "fee", "level", "slack", "room", "short", "long", "near_pickup", "near_delivery", "private_pickup", "private_delivery", "premium", "pay", "friday", "backlog"]
EXTRA = ["tight", "day_left", "local", "weekday", "region", "seasoned", "note", "fee_slack", "fee_short", "fee_long", "fee_tight", "fee_pay", "fee_near_pickup"]
fit.ON_TIME_SIGNS[:] = BASE + EXTRA
tables = [fit.orders_table(run, Atlas(wm, run["roster"])) for run in runs]
print(len(runs), "weeks,", sum(len(t) for t in tables), "orders")

def score(names, ridge=1.0):
    total, n = 0.0, 0
    folds = 4
    for k in range(folds):
        train = [r for i, t in enumerate(tables) if i % folds != k for r in t]
        test = [r for i, t in enumerate(tables) if i % folds == k for r in t]
        X = np.array([[r["signs"][s] for s in names] for r in train]); y = np.array([float(r["on_time"]) for r in train])
        w = fit.logistic(X, y, np.array([0.0 if s == "one" else ridge for s in names]))
        Xt = np.array([[r["signs"][s] for s in names] for r in test]); yt = np.array([float(r["on_time"]) for r in test])
        p = np.clip(1 / (1 + np.exp(-Xt @ w)), 1e-6, 1 - 1e-6)
        total -= float(np.sum(yt * np.log(p) + (1 - yt) * np.log(1 - p))); n += len(test)
    return total / n

base = score(BASE)
print(f"base {base:.4f}")
for extra in EXTRA:
    print(f"  + {extra:<16} {score(BASE + [extra]):.4f}  ({score(BASE + [extra]) - base:+.4f})")
for drop in BASE[1:]:
    print(f"  - {drop:<16} {score([s for s in BASE if s != drop]):.4f}  ({score([s for s in BASE if s != drop]) - base:+.4f})")

print("--- combos")
import itertools
for r in [t for tab in tables for t in tab]:
    s = r["signs"]
    s["long2"] = s["long"] ** 2
    s["far"] = float(r["km"] >= 400)
    s["mid_km"] = float(200 <= r["km"] < 400)
    s["slack2"] = s["slack"] ** 2
    s["fee2"] = s["fee"] ** 2
    s["backlog_long"] = s["backlog"] * s["long"]
    s["slack_long"] = s["slack"] * s["long"]
    s["fee_backlog"] = s["fee"] * s["backlog"]
C1 = BASE + ["fee_slack", "region", "fee_long", "day_left"]
print(f"C1 {score(C1):.4f}")
for extra in ["long2", "far", "mid_km", "slack2", "fee2", "backlog_long", "slack_long", "fee_backlog", "fee_tight", "local"]:
    print(f"  C1 + {extra:<14} {score(C1 + [extra]):.4f}")
C2 = [s for s in C1 if s not in ("friday", "private_pickup", "private_delivery", "room")]
print(f"C2 (C1 without friday, private_*, room) {score(C2):.4f}")
