"""Frees the practice slots that stopped runs left behind: a lost SSH session kills a sweep before it can delete its worlds.

    python clean.py          # lists the team's worlds and deletes the plain practice worlds; never a ranking run, never the final
"""
from spread.client import Client, SpreadError

client = Client()
worlds = client.worlds()
print(f"{len(worlds)} worlds")
for world in worlds:
    plain = world["kind"] == "practice" and world.get("boardRun") is None
    print(f"  {world['worldId']}  {world['kind']:<9} level {world['level']}  ranking run {world.get('boardRun')}  ended {world.get('ended')}", end="")
    if not plain:
        print("  kept")
        continue
    try:
        client.world(world["worldId"]).delete()
        print("  deleted")
    except SpreadError as error:
        print(f"  not deleted: {error}")
