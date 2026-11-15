"""Makes the saved weeks small enough to copy over a slow line: drops the drivers' views, which no tool of ours reads.

    python slim.py            # every runs/*.json.gz that still holds views
"""
import glob
import gzip
import json
import os

for path in sorted(glob.glob("runs/*.json.gz")):
    before = os.path.getsize(path)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        run = json.load(f)
    views = sum(1 for e in run.get("events") or [] if e["kind"] == "gig_viewed") + len((run.get("reveal") or {}).get("views") or [])
    if not views:
        continue
    run["events"] = [e for e in run["events"] if e["kind"] != "gig_viewed"]
    if run.get("reveal"):
        run["reveal"].pop("views", None)
    with gzip.open(path, "wt", encoding="utf-8") as out:
        json.dump(run, out)
    print(f"{path[-60:]:<62}{before // 1024:>6} KB -> {os.path.getsize(path) // 1024:>5} KB", flush=True)
