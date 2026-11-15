"""Run dispatch.py configurations on multiple practice weeks, eight at a time, and print a comparison.

    python sweep.py --seeds test-1,test-2 "tag=a" "tag=a,reserve=0"
    python sweep.py --seeds n-1:16 "tag=a" "tag=a,slope=10"        # n-1:16 = n-1, n-2, ..., n-16
    python sweep.py --summary tag=a                                 # summarize runs matching "tag=a", including means, standard errors, and comparisons with the first configuration

A configuration is a comma-separated list of name=value settings. Use "base" for defaults. Completed runs are appended to sweeps.jsonl.
Runs practice weeks only.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Skip matching the euro sign directly because Windows output may decode it incorrectly.
END = re.compile(r"End\s+margin \D*?(-?[\d,]+\.\d+)\s+revenue \D*?(-?[\d,]+\.\d+)\s+(\d+) orders\s+([\d.]+)% on time")
SERVER = re.compile(r"HTTP (5\d\d|429|409)|restart|onnection|timed out|[Tt]imeout|URLError|IncompleteRead|RemoteDisconnected|SSL|Errno|unreachable")
WEEK = re.compile(r"Week: fees x([\d.]+) typical, one car x([\d.]+), two cars x([\d.]+), paired (\d+)% of cars, prices x([\d.]+) list")


def run(job: tuple) -> dict:
    config, level, seed = job
    command = [sys.executable, "dispatch.py", "--level", str(level), "--seed", seed]
    for item in ([] if config == "base" else config.split(",")):
        command += ["--param", item.strip()]
    for pause in (20, 60, 180, 600, 0):  # the practice server restarts now and then (HTTP 502): the week is played again, ever more patiently
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = done.stdout + done.stderr
        match = END.search(out)
        if match or not SERVER.search(out):  # a mistake in the command or in the code comes back at once: waiting mends only the server's troubles
            break
        time.sleep(pause)
    if not match:
        return {"config": config, "seed": seed, "error": out.strip().splitlines()[-2:]}
    week = WEEK.search(out)
    result = {"config": config, "seed": seed, "margin": float(match[1].replace(",", "")), "orders": int(match[3]),
              "on_time": float(match[4]), "ranked": "Not ranked" not in out, "week": [float(x) for x in week.groups()] if week else None}
    with open("sweeps.jsonl", "a", encoding="utf-8") as log:  # one line a week: a long night of sweeps is read back with --summary
        log.write(json.dumps(result) + "\n")
    return result


def summary(words: list) -> None:
    """For each configuration matching all filters, show the week count, mean margin with its standard error, and mean and lowest on-time rates.
    Compare margin against the first configuration on weeks both played."""
    latest: dict = {}
    for line in open("sweeps.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if all(word in r["config"] for word in words):
            latest[(r["config"], r["seed"])] = r
    configs = sorted(dict.fromkeys(config for config, _ in latest), key=len)  # the shortest name is the base: the others are it with one change
    if not configs:
        return print("No matching runs.")
    base = {seed: r for (config, seed), r in latest.items() if config == configs[0]}
    gap_of = lambda config: sum(r["margin"] - base[seed]["margin"] for (c, seed), r in latest.items() if c == config and seed in base) / max(1, sum(c == config and seed in base for c, seed in latest))
    configs = configs[:1] + sorted(configs[1:], key=gap_of, reverse=True)  # the best change first
    print(f"{'configuration':<58}{'weeks':>5}{'margin':>9}{'+-':>6}{'orders':>7}{'on time':>10}{'lowest':>10}{'<92%':>6}{'<91%':>6}{'vs baseline':>12}{'+-':>6}")
    for config in configs:
        rows = {seed: r for (c, seed), r in latest.items() if c == config}
        margins = [r["margin"] for r in rows.values()]
        mean = sum(margins) / len(margins)
        se = (sum((m - mean) ** 2 for m in margins) / max(1, len(margins) - 1) / len(margins)) ** 0.5
        both = [rows[seed]["margin"] - base[seed]["margin"] for seed in rows if seed in base]
        gap = sum(both) / max(1, len(both))
        gap_se = (sum((d - gap) ** 2 for d in both) / max(1, len(both) - 1) / max(1, len(both))) ** 0.5
        print(f"{config:<58}{len(rows):>5}{mean:>9,.0f}{se:>6,.0f}{sum(r['orders'] for r in rows.values()) / len(rows):>7.0f}{sum(r['on_time'] for r in rows.values()) / len(rows):>9.1f}%"
              f"{min(r['on_time'] for r in rows.values()):>9.1f}%{sum(r['on_time'] < 92 for r in rows.values()):>6}{sum(r['on_time'] < 91 for r in rows.values()):>6}{gap:>+12,.0f}{gap_se:>6,.0f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", help="comma-separated seeds (for example, n-1:16 expands to n-1 through n-16)")
    parser.add_argument("--level", type=int, default=8)
    parser.add_argument("--summary", action="store_true", help="summarize existing runs in sweeps.jsonl whose configurations match all filters")
    parser.add_argument("configs", nargs="*")
    args = parser.parse_args()
    if args.summary:
        return summary(args.configs)
    seeds = []
    for item in args.seeds.split(","):
        ranged = re.fullmatch(r"(.*?)(\d+):(\d+)", item)
        seeds += [f"{ranged[1]}{k}" for k in range(int(ranged[2]), int(ranged[3]) + 1)] if ranged else [item]
    jobs = [(config, args.level, seed) for seed in seeds for config in args.configs]  # finish all configurations for each seed so partial sweeps can still be compared
    print(f"Running {len(args.configs)} configurations x {len(seeds)} weeks = {len(jobs)} runs, 8 at a time...", flush=True)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(run, jobs))
    print(f"\n{'configuration':<44}{'weeks':<10}{'margin':>9}{'orders':>7}{'/don':>7}{'on time':>10}{'fee':>8}{'1 car':>7}{'2 cars':>7}{'paired':>6}{'price':>7}")
    for config in args.configs:
        rows = [r for r in results if r["config"] == config]
        good = [r for r in rows if "error" not in r]
        for r in rows:
            if "error" in r:
                print(f"{config:<44}{r['seed']:<10}ERROR: {' | '.join(r['error'])}")
            else:
                k = r.get("week")
                more = f"{k[0]:>8.3f}{k[1]:>7.3f}{k[2]:>7.3f}{k[3]:>5.0f}%{k[4]:>7.3f}" if k else ""
                print(f"{config:<44}{r['seed']:<10}{r['margin']:>9,.0f}{r['orders']:>7}{r['margin'] / max(1, r['orders']):>7.1f}{r['on_time']:>9.1f}%{more}")
        if len(good) > 1:
            mean = sum(r["margin"] for r in good) / len(good)
            weeks = [r["week"] for r in good if r.get("week")]
            more = "".join(f"{sum(k[i] for k in weeks) / len(weeks):>{w}.3f}" for i, w in ((0, 8), (1, 7), (2, 7))) + f"{sum(k[3] for k in weeks) / len(weeks):>5.0f}%{sum(k[4] for k in weeks) / len(weeks):>7.3f}" if weeks else ""
            print(f"{'  => average':<44}{'':<10}{mean:>9,.0f}{sum(r['orders'] for r in good) / len(good):>7.0f}{'':>7}{sum(r['on_time'] for r in good) / len(good):>9.1f}%{more}   lowest {min(r['on_time'] for r in good):.1f}%, {sum(r['ranked'] for r in good)}/{len(good)} ranked")


if __name__ == "__main__":
    main()
