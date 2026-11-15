# Spread final-day plan

Written at 11:00 Vietnam time on Sunday, November 15. All times below are **Vietnam time** (Helsinki + 5 hours), except where marked otherwise.

## 1. Two stages

| Stage | When | Assessment | Requirements |
|---|---|---|---|
| 1. Qualify in the top 10 | 14:00–14:35, one secret level-8 week | Margin for that week | At least 90% of orders on time and a top-10 margin |
| 2. Place in the challenge's top 3 | 15:30–19:00, jury meets the 10 teams | Elegant, clear, creative, robust | Submission by 15:00 and a presentation |

The rules state: *"Reaching the top 10 is enough. After that, the jury judges how you built your system, and your margin no longer counts."*

- Our internal margin target is **top 5**, which gives us a buffer if other teams improve. Fourth and ninth place count the same with the jury.
- A top-three finish remains uncertain. The plan reduces operational mistakes, improves our chances of qualifying, and gets the presentation ready before the final starts.

## 2. Where we stand against other teams

### 2.1 Five-week totals

| Round (Helsinki time) | Our margin | Rank | 1st place | 10th place |
|---|---|---|---|---|
| Saturday 18:00 | €82,454 | 3 / 67 | €94,445 | €75,405 |
| Saturday 21:00 | €96,850 | 2 / 55 | €105,424 | €86,201 |
| Sunday 03:00 | €79,317 | About 5 / 48 | €88,416 | €76,873 |

### 2.2 Week-by-week variability

The final is **one week**. Here are our weekly results against the top 15 teams in the Sunday 03:00 round.

| Week | Our margin | Top team's margin | 10th team that week | Our rank |
|---|---|---|---|---|
| 1 | 16,830 | 18,156 | 15,256 | 5 |
| 2 | 15,967 | 16,197 | 14,246 | 2 |
| 3 | 10,992 | 12,520 | 11,045 | 10 |
| 4 | 17,532 | 20,920 | 19,636 | **15** |
| 5 | 17,995 | 19,346 | 17,077 | 4 |

- Five strong teams had yet to play that round. Including them would push each rank down another 3 to 5 places.
- With this morning's version, we estimate a **55 to 70%** chance of placing in the top 10 in any given week. We placed in the top 8 in all five weeks of the Saturday 21:00 round.
- Across the same five weeks, the organizers' best system earned €56,128 and the starter kit lost €362,463.

### 2.3 How the leading teams earn their margin

| Team | Orders per week | € per order |
|---|---|---|
| Competitor A | 473 | 43.3 |
| Competitor B | 464 | 41.4 |
| Competitor C | 402–416 | 42.5–45.5 |
| Competitor D | 417 | 43.9 |
| **Our team** | **458–526** | **34.6–36.8** |

The leading teams take fewer orders and earn more per order. They did especially well in the high-margin week 4. We took 275 orders in the first two days, and our on-time rate fell to 87.2% by Wednesday.

The 11:00 analysis in Section 3 checked the quote prices and traced the shortfall to a wave of late cars in the first two days. The bot then stopped taking most new orders for nearly two days. The `ease` experiment is still running, and enabling it depends on the results.

## 3. Margin work for the remaining two hours

As throughout the challenge, enable a change only if it wins on the same weeks under the rule set in advance.

**Adoption rule.** The gain must be ≥ max(€250, 1.5 × standard error) across 69 weeks, with no additional weeks below 91% on time. For the `lane_cap` safeguard, require at least a 1 percentage point gain in the on-time rate on `night-30` and a nonnegative total across all other weeks.

| Task | Status | Decision |
|---|---|---|
| `backup=1.26` (demand curve for competitor outages) | Tested at €17,637 versus €17,642 | **Leave off** |
| `lane_cap=8` (limit waiting cars on long lanes) | Only 3/60 weeks changed. The worst week gained €1,464 and improved from 90.0% to 91.4% on time. The other two lost €173 and €120 | **Enable** |
| `morning=true` (repost waiting gigs each morning) | +€181 ± 84 across 115 weeks. The worst week reached 91.6% | **Enable**. The gain was below €250 and repeated on 46 new weeks |
| Analyze week 4 of this morning's round | Complete. After 30 late cars in the first two days, the price of a late order rose to €2,463–4,800 and the bot declined 41% of Wednesday's requests | Test `ease` |
| `ease=0.01` with `ease_top=0.06` | Running on 60 weeks | Enable if the gain is ≥ €250 and ≥ 1.5 standard errors, with every week at or above 91% |
| Last ranking round (opens at 11:00) | Play with the locked configuration | Dress rehearsal. Keep the configuration after this round |

**Lock the configuration at 12:30.** Keep that configuration for the final.

If `ease` falls short of the adoption rule, use the locked build (`4ce23b14` or `91dda7db`, which behave identically). It combines last night's build with `morning` and `lane_cap`. The previous build is available on the server as `dispatch_c4a795fb.py` for rollback.

## 4. Schedule

| Time | Task | Owner |
|---|---|---|
| 11:00–11:20 | Paste the output of `weeks.py` and `board.py "<baseline system name>" 3` and the summary line. Copy the ranking-week files with SCP | Triết |
| 11:00–12:15 | Build the slides using [the pitch notes](../presentation/PITCH_NOTES.md) | Slide team |
| 11:20–12:00 | Read the results, analyze week 4, and decide on `lane_cap` | Claude |
| 12:00–12:15 | Play the last ranking round (5 weeks, in tmux, without pressing Ctrl-C) | Triết |
| 12:15–12:30 | Run the remaining comparisons for the slides (starter, pairing off, menu off) | Triết |
| **12:30** | **Lock the configuration** | Whole team |
| 12:30–13:10 | Create the public repository, push the code and README, and check the link in a private browser window | Triết + one teammate |
| 12:30–13:30 | Rehearse twice using Section 5 of the pitch notes and quiz each other on the 12 questions in Section 6 | Presenters |
| **13:15** | **Start the final** (Section 5) | Triết |
| 13:30 | Final registration closes. Check that the bot prints `Final world ...` or is waiting | Triết |
| 14:00–14:35 | Final runs. **Observe the server without intervening** | Triết |
| 14:35–14:50 | Add the results to the slides and README, then export the PDF | Whole team |
| **14:50** | **Submit the hash, code link, and slides** | Triết |
| 15:00 | Submission deadline | |
| 15:30–19:00 | Meet the jury if we qualify in the top 10 | Whole team |

## 5. Commands for the final

On the server, attach to the existing tmux session and run the engine from its repository directory.

```bash
tmux attach -t main
cd ~/spread-bot/engine
source .venv/bin/activate
set -a; source .env; set +a
md5sum dispatch.py | cut -c1-8
python board.py | tail -3
bash final.sh
```

- `md5sum` must return the hash of the locked build.
- A successful `board.py` run confirms the key is loaded.
- Start the bot early. It waits for the final to begin.
- Detach from tmux with `Ctrl-b` followed by `d`. Reattach with `tmux attach -t main`.

### Troubleshooting during the final

| Issue | Action |
|---|---|
| SSH disconnects | Reconnect over SSH and run `tmux attach -t main`. The bot continues running in tmux |
| Bot stops with an error | Let `final.sh` restart it after 3 seconds. It reconnects to the same week |
| Restart loop reports `SPREAD_KEY is not set` | Press Ctrl-C twice, run `set -a; source .env; set +a` in `engine/`, then run `bash final.sh` |
| Server goes down | Switch to the laptop. In PowerShell, enter `engine/`, activate the environment, load the key with `. .\load-env.ps1`, and run `python dispatch.py --final`. The bot rebuilds orders and gigs from the organizers' server |
| The on-time rate drops midweek | **Let the bot run.** It raises the cost of risky orders. Stopping it loses incoming requests |

Under the rules, when the bot stops, competitors receive new requests and drivers continue fulfilling existing orders. Each second of downtime costs potential revenue.

## 6. Submission (before 15:00)

- [ ] **Submission hash.** Get it from the team page and copy it into a file at 13:30.
- [ ] **Code link.** Use a public repository with `README.md` and the engine files `dispatch.py`, `world.py`, `fit.py`, `model.json`, `notes_reader.py` (retain its MIT header), `sweep.py`, `weeks.py`, `night.py`, `final.sh`, `check_final.py`, `replay_test.py`, and `restart_test.py`. Keep `.env`, `runs/`, and `.venv/` private.
- [ ] **Slides.** Submit 5 to 10 slides as a PDF. Claude's Saturday deck is available as a fallback and needs four figures filled in.
- [ ] Cite the [experiment log](../research/EXPERIMENT_LOG.md) in the slides and README for the decisions on driver capacity, the six-hour fee step, and direct offers. Cite the [dealer-note reader's copyright notice and MIT license](../../engine/notes_reader.py). Credit Claude for writing most of the code and analysis.

## 7. Scenarios

**A. Top 10 (main expectation).** Submit on time and present from 15:30 using the pitch notes. Lead with the central idea, paired measurements for each decision, 69 unseen weeks, and the system's limitations.

**B. Ranked outside the top 10.** Submit everything by 15:00. The rules require every team to submit, and the organizers will replay each week to verify scores. Rankings may change.

**C. Final week below 90% on time.** The week is unranked. Submit anyway. The estimated probability is 1 to 2%, based on one of 69 practice weeks coming in at exactly 90.0%.

## 8. After the final

- Delete the Verda servers, including the unused V100 instance, to stop billing.
- Save `sweeps.jsonl`, `final.log`, and `runs/` before deleting the servers. They contain the evidence for the figures on the slides.
