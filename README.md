# Spread dispatch desk (Bahn challenge, Junction 2026)

A dispatch desk for the Spread world at level 8. One idea runs through it:

> **A car costs its fee, plus its risk of arriving late, plus the driver it takes from the cars that already wait.**

## Result

| | |
|---|---|
| The final | to be filled in after 09:35 Helsinki |
| Best ranking round | €96,850 for five secret weeks, place 2 of 55 ranked teams (Saturday 21:00) |
| Latest ranking round | €79,317 for five secret weeks (Sunday 03:00), against €56,128 for the organizers' best system and −€362,463 for their starter kit |
| Practice | €17,702 a week (± 386) on 117 level-8 weeks the desk had never played. All 117 ranked, 95.7% of orders on time |

## How the desk decides

1. **Cost.** The fee our model expects to pay in the end, plus the refund times the chance of a late car, plus the car's use of the room under the 90% delivery minimum.
2. **Floor.** Cost × 1.10. The driver this car takes is one that the waiting cars do not get.
3. **Price.** The multiple of the list price where (price − floor) × P(yes) is largest. P(yes) follows a price level learned from this week's answers: the week, the day, the dealer, the two towns, and the dealer's trust in us.
4. **Menu.** Every option the car can make, each at the same margin. The dealer picks the speed.
5. **Gig.** One fee from the model. One step up after six working hours, and again 8 and 5 working hours before the last pickup. The urgent fee (1.6 × typical) at the deadline warning. The typical fee again once the last pickup has passed. A second car joins the gig when it starts where the first ends.

The three formulas:

$$p^{*} = \arg\max_{p}\; \big(p - c\,(1+r)\big)\cdot P(\text{yes}\mid p), \qquad r = 0.10$$

$$c = \mathbb{E}[\text{fee paid}] + P(\text{late})\cdot \text{refund} + \big(P(\text{late}) - 4\%\big)\cdot \lambda$$

$$f^{*} = \arg\min_{f}\; \mathbb{E}[\text{fee paid}\mid f] + P(\text{late}\mid f)\cdot L$$

Here λ is the price of one late order. It is near zero while the week expects far fewer late orders than the 4% we allow ourselves, and it rises steeply near that share. So the 90% delivery minimum is a price, not a rule.

## What each idea earned

Worlds repeat to the euro: the same seed gives the same week. So every comparison is on the same weeks, with one change. ± is one standard error of the paired difference.

| Idea | On the 8 weeks we tuned on | On weeks the desk had never played |
|---|---|---|
| A margin floor of 10% above cost (the price of a driver) | €16,415 → €17,578 a week (8 of 8 weeks), on time 95.2% → 96.0% | +€809 ± 121 on 117 weeks, on time 95.1% → 95.7% |
| Late is late: a car past its last pickup goes back to the typical fee | €15,551 → €16,415 (8 of 8 weeks), on time 94.6% → 95.2% | +€453 ± 68 on 115 weeks, on time unchanged |
| The price of lateness capped at €150 inside the fee choice | +€126 | +€149 ± 70 on 115 weeks |
| One fee per gig from a model of our own weeks | €12,172 → €13,572 | |
| Euro gaps between options, price level by lane | €13,572 → €14,740 | |
| A readiness check before two cars share a gig | €14,740 → €15,551 | |
| Gigs left from an earlier day are posted again each working morning | | +€181 ± 84 on 115 weeks; the worst week 90.0% → 91.6% on time |
| No more than 8 of our cars waiting on one long lane | | changes 3 of 60 weeks: +€1,464 and 90.0% → 91.4% in one, −€173 and −€120 in two others |

Tuned on 8 weeks: €17,704 a week. Played once on 117 new weeks: €17,702.

The [experiment log](docs/research/EXPERIMENT_LOG.md) records every run, what changed, what we observed, and what we decided.

## How we measured

- **Paired weeks.** Same seeds, one change, the difference and its standard error.
- **A rule set before each test.** A change is taken when it gains at least €250 a week and 1.5 standard errors, and adds no week under 91% on time.
- **Weeks never played.** Choices were made on 8 fixed weeks, then checked on new ones.
- **A switch for every change.** Each change is a parameter that is off by default. With it off, a new build must act exactly like the old one: `replay_test.py` replays a saved week through both and compares every action.
- **A restart.** In a test final we stopped the desk on purpose. It rebuilt its books from the world's history and its own journal: €18,599, 95.8% on time, 0 of 1,030 requests missed.

## What did not work

| Tried | Result, € a week |
|---|---|
| A margin floor that follows the queue | −380 to −820 |
| A margin floor that follows the week's late share | −16 to −346 |
| Cheaper early orders to build a dealer's trust | −381 |
| On-time target 95% instead of 96% | +157, but 3 weeks under 91% |
| Urgent fee 1.4 × or 1.8 × instead of 1.6 × | −505, −125 |
| Holding a new car back to wait for a partner | +114, but one week not ranked |
| A separate demand curve for the competitor's outage day | +74 ± 114 |
| The outage rule itself | −59 ± 94 without it: nothing we could measure |
| Nine more parts in the dealers' price level | no better forecast |
| A sign for crowded towns or lanes in the on-time model | no better forecast on 21 weeks |

## Limits

- **One dealer's batch for a far town.** 18 cars from Joensuu to Oulu, sold in one morning, found 1 driver in time. That week, 1 of 117, ended at exactly 90.0% on time. We found no general sign for it, so a cap now refuses the rest of such a batch.
- **The richest weeks.** In the Sunday 03:00 round, week 4, we earned €17,532 where the teams around us earned €19,000 to €22,400. After two days with 30 late cars, our price of a late order rose from under €100 to €2,463, and the desk declined 41% of Wednesday's requests. That price looks only backwards.
- **A week whose drivers are far from the weeks we fitted.** The fee model extrapolates.
- **Downtime.** The journal restores the desk, not the quotes it missed.
- A flatter demand curve (slope 12) still earns more than the best-fitting one (16). We cannot fully explain it.

## Files

| File | What it is |
|---|---|
| `dispatch.py` | The desk: quotes, fees, pairs, the learner, the restart. Every number in `Params` says where it was measured |
| `world.py` | The facts of a world: roads, opening hours, where drivers live, and the signs the fee model reads |
| `fit.py` | Fits `model.json` from saved weeks: the on-time model, the fee paid in the end, the dealers' curve |
| `model.json` | The fitted model the desk plays with |
| `notes_reader.py` | The MIT-licensed dealer-note reader used in pickup and pairing decisions |
| `sweep.py`, `weeks.py` | Many configurations on many seeds, and the paired comparison week by week |
| `night.py` | A night of sweeps that takes nothing unless a change clears its noise |
| `final.sh`, `check_final.py` | The final with a restart loop, and a check of what the desk answered in time |
| `replay_test.py`, `restart_test.py` | A saved week replayed through a new build; a desk rebuilt from the world's history and its journal |
| `board.py`, `clean.py` | The ranking table; freeing practice slots |
| `study.py`, `pairs_study.py`, `cv.py`, `analyze.py`, `v4_look.py`, `slim.py` | Analyses of saved weeks |
| `dispatch_v1.py` to `dispatch_v3x.py` | Earlier versions, kept for the record |
| [Architecture](docs/architecture/ARCHITECTURE_v1.md) | How the dispatch desk works |
| [Experiment log](docs/research/EXPERIMENT_LOG.md) | Runs, observations, and strategy decisions |
| [Pitch notes](docs/presentation/PITCH_NOTES.md) | Slide guide, speaker scripts, and jury questions |
| [Final-day plan](docs/operations/FINAL_DAY_PLAN.md) | Final-day schedule and operations |

## Run it

Enter `engine/` from the repository root. Use a Python virtual environment with the organizers' `spread` package and set `SPREAD_URL` and `SPREAD_KEY`. On PowerShell, `. .\load-env.ps1` loads them from `engine/.env`.

```
python dispatch.py --level 8 --seed test-1                       # one practice week
python dispatch.py --level 8 --seed test-1 --param reserve=0     # the same week with one change
python sweep.py --seeds n-1:16 "tag=a" "tag=a,reserve=0"         # paired, 16 weeks each
python sweep.py --summary tag=a
python weeks.py "tag=a" "tag=a,reserve=0"                        # week by week
bash final.sh                                                    # the final, with a restart loop
```

