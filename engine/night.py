"""The night's work on practice weeks, in two stages. It never plays a ranking run or the final.

Stage 1: the configuration in dispatch.py and model.json, and one change at a time, each on the same fresh weeks (seeds night-1, night-2, ...).
Stage 2: the changes that earned their place, all together, against the base on other fresh weeks (seeds dawn-1, ...), and the same
         with each of them left out in turn: a change stays only if the whole is worse without it.

    python night.py 4.5 9    # stage 1 for four and a half hours, then stage 2; nine hours after the start nothing is started any more
    python sweep.py --summary tag=night        # at any time, from another window: every change against the base, best first
    python sweep.py --summary tag=dawn         # the same for stage 2
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import sweep

BASE: list = []  # changes that every run of the night carries, for example ["slope=10"]
FAMILIES = {  # of each family at most one change is taken: its members answer the same question
    "reserve": ["reserve=0", "reserve=0.05", "reserve=0.15", "reserve_tight=1", "reserve=0.15,reserve_tight=1", "reserve_tight=2"],
    "slope": ["slope=10", "slope=14"],
    "on time": ["on_time=0.95", "on_time=0.97"],
    "calm": ["calm_eur=300", "calm_eur=75"],
    "late": ["late_fee=0"],
    "urgent": ["urgent_fee=1.8"],
    "fees": ["fees=0.85;1.0;1.15;1.3;1.5"],
    "steps": ["look_h=0", "look_h=3"],
    "morning": ["morning=true"],
    "hold": ["pair_hold=60"],
    "pair km": ["pair_km=50"],
    "pair hours": ["pair_max_h=7"],
    "pair fee": ["pair_fee=0.7"],
    "outage": ["outage=0"],
}
LOWEST = 91.0  # a change is not taken if any of its weeks ends under this share on time: under 90% a week is not ranked


def name(tag: str, changes: list) -> str:
    return ",".join([f"tag={tag}"] + BASE + changes)


def play(jobs: list, until: float) -> None:
    """Eight weeks at a time, in the order given; a week whose turn comes after `until` is not started."""
    played = {(week["config"], week["seed"]) for rows in (weeks("night"), weeks("dawn")) for config in rows.values() for week in config.values()}

    def one(job: tuple):  # a week already in sweeps.jsonl is not played again: the night can be stopped and started
        return sweep.run(job) if time.time() < until and (job[0], job[2]) not in played else None
    with ThreadPoolExecutor(8) as pool:
        for done, result in enumerate(pool.map(one, jobs), 1):
            if result and "error" in result:
                print(f"  ERROR {result['config']} {result['seed']}: {' | '.join(result['error'])}", flush=True)
            if done % 40 == 0:
                print(f"  {time.strftime('%H:%M')}  {done}/{len(jobs)} runs", flush=True)


def weeks(tag: str) -> dict:
    """config -> seed -> the logged week, for the configurations of this tag."""
    found: dict = {}
    for line in open("sweeps.jsonl", "a+", encoding="utf-8") if not os.path.exists("sweeps.jsonl") else open("sweeps.jsonl", encoding="utf-8"):
        week = json.loads(line)
        if week["config"].split(",")[0] == f"tag={tag}":
            found.setdefault(week["config"], {})[week["seed"]] = week
    return found


def gain(rows: dict, base: dict) -> tuple:
    """Mean and standard error of the margin against the base, over the weeks both played."""
    gaps = [rows[seed]["margin"] - base[seed]["margin"] for seed in rows if seed in base]
    if len(gaps) < 8:
        return 0.0, float("inf"), len(gaps)
    mean = sum(gaps) / len(gaps)
    return mean, (sum((gap - mean) ** 2 for gap in gaps) / (len(gaps) - 1) / len(gaps)) ** 0.5, len(gaps)


def chosen() -> list:
    """From stage 1: in each family the change that gained most, if its gain is at least 1.5 standard errors and EUR 250 a week,
    and none of its weeks ended under LOWEST on time."""
    found = weeks("night")
    base, taken = found.get(name("night", []), {}), []
    for family, members in FAMILIES.items():
        best = None
        for change in members:
            rows = found.get(name("night", [change]), {})
            mean, error, count = gain(rows, base)
            low = lambda played: sum(week["on_time"] < LOWEST or not week["ranked"] for seed, week in played.items() if seed in rows and seed in base)
            safe = low(rows) <= low(base)  # no more weeks near the 90% line than the base has on the same weeks
            print(f"  {family:<10} {change:<28} {count:>3} weeks  {mean:>+7,.0f} +-{error:>5,.0f}  lowest {min((week['on_time'] for week in rows.values()), default=0):.1f}%{'' if safe else '  (fails safety check)'}")
            if safe and mean >= max(250.0, 1.5 * error) and (best is None or mean > best[0]):
                best = (mean, change)
        taken += [best[1]] if best else []
    return taken


def main() -> None:
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0   # stage 1
    total = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0   # both stages: after this many hours nothing is started any more
    start = time.time()
    end = start + total * 3600
    changes = [[]] + [[change] for members in FAMILIES.values() for change in members]
    print(f"{time.strftime('%H:%M')}  Stage 1: {len(changes)} configurations for {hours} hours (no new runs after {total} hours)", flush=True)
    play([(name("night", change), 8, f"night-{seed}") for seed in range(1, 121) for change in changes], min(end, start + hours * 3600))
    print(f"\n{time.strftime('%H:%M')}  Stage 1 complete:", flush=True)
    try:
        sweep.summary(["tag=night"])
        taken = chosen()
    except Exception as error:  # the night goes on with what it has
        print(f"  selection failed: {error!r}", flush=True)
        taken = []
    print(f"\n{time.strftime('%H:%M')}  Stage 2 keeps {taken or 'no changes'}", flush=True)
    if not taken:  # nothing earned its place: more weeks of stage 1 say more than a second stage of the base alone
        play([(name("night", change), 8, f"night-{seed}") for seed in range(121, 400) for change in changes], end)
    else:
        finals = [[], taken] + ([[other for other in taken if other != change] for change in taken] if len(taken) > 1 else [])
        with open("night_choice.json", "w", encoding="utf-8") as out:
            json.dump({"taken": taken, "configs": [name("dawn", changes) for changes in finals]}, out, indent=1)
        play([(name("dawn", changes), 8, f"dawn-{seed}") for seed in range(1, 600) for changes in finals], end)
    print(f"{time.strftime('%H:%M')}  Time is up. All runs have ended.", flush=True)


if __name__ == "__main__":
    main()
