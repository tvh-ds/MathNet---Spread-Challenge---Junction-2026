"""Week by week: where does a configuration differ from the base? (Worlds repeat to the euro, so a week that differs was changed by the configuration.)

    python weeks.py "tag=night" "tag=night,lane_cap=8" "tag=night,lane_cap=6"
"""
import json
import sys

rows = {}
for line in open("sweeps.jsonl", encoding="utf-8"):
    r = json.loads(line)
    rows[(r["config"], r["seed"])] = r
base = sys.argv[1]
for config in sys.argv[2:]:
    both = sorted(seed for (c, seed) in rows if c == config and (base, seed) in rows)
    gaps = [rows[(config, seed)]["margin"] - rows[(base, seed)]["margin"] for seed in both]
    if not gaps:
        print(f"{config}: no week in common with {base}")
        continue
    mean = sum(gaps) / len(gaps)
    se = (sum((g - mean) ** 2 for g in gaps) / max(1, len(gaps) - 1) / len(gaps)) ** 0.5
    changed = [seed for seed, gap in zip(both, gaps) if abs(gap) > 0.5]
    low = lambda name: sorted(rows[(name, seed)]["on_time"] for seed in both)[:3]
    unranked = lambda name: sum(not rows[(name, seed)]["ranked"] for seed in both)
    print(f"\n{config}: {len(both)} weeks, {mean:+,.0f} +- {se:,.0f} a week; {len(changed)} weeks differ; lowest on time {low(config)} (base {low(base)}); not ranked {unranked(config)} (base {unranked(base)})")
    for seed in sorted(changed, key=lambda seed: -abs(rows[(config, seed)]["margin"] - rows[(base, seed)]["margin"]))[:12]:
        a, b = rows[(base, seed)], rows[(config, seed)]
        print(f"   {seed:<10} {a['margin']:>8,.0f} -> {b['margin']:>8,.0f} ({b['margin'] - a['margin']:>+7,.0f})   orders {a['orders']} -> {b['orders']}   on time {a['on_time']:.1f}% -> {b['on_time']:.1f}%")
