"""The practice rankings at level 8: the round before and the round that is open, with the first teams and ours: the margin of each week,
the orders a week and the margin an order (how the teams ahead earn theirs: by volume or by margin).

    python board.py              # only reads the rankings; plays nothing
    python board.py MathNet 20   # our name (any part of it) and how many teams to list
"""
import sys

from spread.client import Client

name = (sys.argv[1] if len(sys.argv) > 1 else "mathnet").lower()
shown = int(sys.argv[2]) if len(sys.argv) > 2 else 15
board = Client().board(8)
for which in ("previous", "current"):
    season = board.get(which)
    if not season:
        continue
    teams = season["teams"]
    ranked = sorted((team for team in teams if team["rank"]), key=lambda team: team["rank"])
    done = [team for team in ranked if team["played"] >= 5]
    print(f"\n{which}: {season['name']} (started {season['startedAt']}): {len(teams)} teams, {len(ranked)} ranked, {len(done)} with five weeks")
    for team in teams:
        ours = name in team["name"].lower()
        if not ours and not (team["rank"] and team["rank"] <= shown):
            continue
        runs = sorted(team["runs"], key=lambda run: run["run"])
        weeks = " ".join(f"{run['marginCents'] / 100:>7,.0f}{'' if run['ranked'] else '!'}" for run in runs)
        orders = sum(run["wonOrders"] for run in runs) / max(1, len(runs))
        weeks += f"   | {orders:.0f} orders a week, {sum(run['marginCents'] for run in runs) / 100 / max(1, sum(run['wonOrders'] for run in runs)):.1f} an order"
        margin = "      -" if team["marginCents"] is None else f"{team['marginCents'] / 100:>9,.0f}"
        share = "" if team["onTimeShare"] is None else f"{team['onTimeShare']:.1%}"
        print(f"  {str(team['rank'] or '-'):>3}  {team['name'][:24]:<24} {team['played']} weeks {margin}  {share:>6}   {weeks}{'   <== ours' if ours else ''}")
