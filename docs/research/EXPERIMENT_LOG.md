# Spread experiment log

Each row records a server run or an analysis of saved weeks, including what changed, what we observed, what we decided, and which strategy it tested.

Times are in Vietnam time unless specified otherwise. Amounts are level-8 profit in euros per week, averaged across the weeks in the "Test weeks" column. "±" denotes one standard error of the paired difference, using the same weeks with one change at a time.

## Strategy codes

| Code | Strategy | Description |
|---|---|---|
| S0 | Baseline | The starter kit with fixed rules |
| S1 | Dealers | Learn the prices dealers accept during the week and offer a menu of delivery speeds |
| S2 | Driver fees | Choose one fee per gig using a model fitted on our own weeks |
| S3 | Pricing the 90% minimum | Include the minimum on-time rate in each car's cost |
| S4 | Pairing cars | Assign two cars to one driver when the second starts where the first ends |
| S5 | The price of a driver | Require each order to earn 10% above cost |
| S6 | Late is late | Stop paying the urgent fee once a car has passed its last pickup |
| S7 | Safeguards | Limit batches on one lane, repost gigs each morning, and recover from restarts |
| M | Measuring the world | Randomize decisions during practice weeks to collect data and fit models |

## Results as of Sunday at 11:15

| Measure | Result |
|---|---|
| 8 tuning weeks (halal-09 through halal-16) | €17,704 |
| 117 previously unseen weeks (Saturday night build) | €17,702 ± 386, 95.7% on time, 117/117 ranked |
| Best ranking round | €96,850, 2nd of 55 (Saturday 21:00 Helsinki time) |
| Latest ranking round | €79,317 (Sunday 03:00). The organizers' best system earned €56,128 and their starter kit lost €362,463 |

---

## Phase 1 · Fixed rules and the first price learner (v1–v3)

Test weeks were `test-1` and `test-2`. The goal was to get a working bot and understand how the settings affected it.

| Version / configuration | Result | Orders | On time | Observation | Decision | Strategy |
|---|---|---|---|---|---|---|
| v1 with `fee=1.0` and fixed prices | 6,446 | 244 | 97.6% | Very safe, with few orders | Initial baseline | S0 |
| v2 with `learn=true, fee=1.0` | 7,679 | 285 | 97.9% | Learning prices during the week gained 1,233 and preserved on-time performance | Keep | S1 |
| v2 with `fee=0.95, min_slack_h=5` | 7,814 | 326 | 95.1% | A slightly lower fee still worked | Keep | S2 |
| v2 with `fee=0.9, reserve=0.05` | 6,773 | 354 | 94.0% | A fee of 0.9 × typical made cars wait longer and increased lateness | Drop | S2 |
| v2 with `min_slack_h=3` (accept more urgent cars) | 6,542 | 378 | 92.5% | The extra orders were risky | Drop | S3 |
| v2 with `max_km=700` added | 4,200 | 363 | 87.9% | **0/2 weeks ranked.** Very long lanes hurt the on-time rate | Drop | S3 |
| v2 with `late_eur=40, max_backlog=70` | 5,813 | 439 | 89.1% | 1/2 weeks went unranked because the lateness penalty was too low | Drop | S3 |

**Phase 1 lesson.** Higher order volume can lower profit. The 90% cutoff was close, and hand-tuning constants had limited room for improvement.

---

## Phase 2 · Measuring the world and fitting models (M)

| Run | Method | Result | Used for |
|---|---|---|---|
| 16 `explore` weeks (`ex-1` through `ex-16`) | Random quotes at 1.0–1.9 × list price and random fees | −4,381 per week, 77.8% on time, expected in an unranked experiment | Dealer demand curve, or acceptance probability by price |
| 16 `try_fees` weeks (`tf-1` through `tf-16`) | Play normally and randomize the opening fee across six levels | 8,119 per week, 95.1% on time | Models for on-time delivery and actual fees paid |
| `fit.py` → `model.json` | Logistic regression for on-time delivery on 7,235 cars, linear regression for fees paid, and a demand curve based on 16,232 quotes | With a driver before the warning, 2.4% were late. Without one, 58.8% were late. A late order refunded 0.47 × list price on average | S1, S2 |
| Leave-one-week-out cross-validation | Try extra features in the on-time model | Kept the current 26 features. Extra features failed to reduce log loss | S2 |

**Observation.** The typical fee is a threshold. Opening at 0.70 × typical yielded 87.4% on time and 1.00 × yielded 97.4%. Higher fees added almost nothing.

---

## Phase 3 · Optimizing each decision in v4

| Version / change | Test weeks | Result | Observation | Decision | Strategy |
|---|---|---|---|---|---|
| v4 baseline | test-1 | 8,451 (93.7%) | Models replaced constants | Keep | S2 |
| v4 with `on_time=0.90` | test-1 | 5,553 (89.5%) | **Unranked.** Aiming for exactly 90% left too little room | Drop | S3 |
| v4 with `on_time=0.92` / `0.94` | test-1 | 6,685 / 6,459 | Lower targets reduced profit | Choose 0.96 | S3 |
| v4.2 baseline | test-1,2 | 9,110 (97.1%) | | | |
| v4.2 with `pairs=true` | test-1,2 | 9,809 (96.5%) | Pairing gained 699 | Keep | S4 |
| v4.4 with `pairs=true` | halal-09, 12 | 16,200 (91.8%) | Two weeks were too few to compare with the eight-week baseline. Used to study which two-car gigs found a driver (`pairs_study.py`) | Study further | S4 |
| Switch from fixed fee tiers to model-selected fees | 8 tuning weeks | 12,172 → 13,572 | +1,400 | Keep | S2 |
| Fixed euro gaps between options and price levels by lane | 8 tuning weeks | 13,572 → 14,740 | +1,168. Dealers valued each slower option a fixed number of euros less (€15, then €8) | Keep | S1 |
| Check readiness when pairing | 8 tuning weeks | 14,740 → 15,551 | +811. There were 17 gigs pairing a car that was not ready with a car on an earlier deadline. 18 cars were 14–89 hours late | Keep | S4 |

---

## Phase 4 · Saturday evening and hidden costs (v4.9e → v4.9g)

Test weeks were halal-09 through halal-16. The v4.9e baseline was 15,551.

| Time | Run | Change | Result | Observation | Decision | Strategy |
|---|---|---|---|---|---|---|
| 23:16 | 7 | `late_fee`, `slope=10`, `pair_hold=60` | `late_fee` returned "No parameter". Slope 10 earned 15,633 and pair hold earned 14,085 | A stalled upload left the old version on the server. We checked MD5 hashes from then on | Fix the process | — |
| 23:55 | 9 | `late_fee=1.0` | **16,415 (+864, 8/8 weeks)**, 94.6% → 95.2% on time | 15.1 cars per week found drivers after the last pickup. All were late and paid 1.6 × typical | **Keep** | S6 |
| 23:55 | 9 | `late_fee=0.85` / `1.15` | −257 / −246 relative to 1.0 | 1.0 × worked best | Drop | S6 |
| 23:55 | 9 | `invest=1.0` (discount to build trust) | −381 | A 1% gain per on-time order fell short of covering the discount | Drop | S1 |
| 00:06 | 10 | `reserve=0.1` | **17,578 (+1,163, 8/8)**, 527 → 483 orders, 95.2% → 96.0% on time | Fewer orders brought higher profits and better on-time performance. Drivers were scarce | **Keep** | S5 |
| 00:06 | 10 | `reserve=0.2` / `0.3` | 17,317 / 15,837 | The peak was around 0.10–0.13 | Choose 0.1 | S5 |
| 00:06 | 10 | `slope=8` / `6` (with reserve at 0) | 16,813 / 16,108 | A flatter demand curve captured only a third of the reserve's gain | Drop | S5 |
| 00:17 | 11 | `reserve_q` (based on queue length) | −380 to −820 | Long queues pushed prices too high just as dealers were buying | Drop | S5 |
| 00:17 | 11 | `on_time=0.95` | −266 | | Drop | S3 |
| 00:17 | 11 | `urgent_fee=1.4` | −505 | The lower urgent fee left urgent cars without drivers | Drop | S2 |
| 00:36 | 12 | `calm_eur=150` | **17,704 (+126)** | Higher fees mainly shifted drivers between our own cars | **Keep** | S2 |

---

## Phase 5 · Saturday night tests on unseen weeks (v4.9h)

| Time | Run | Method | Result | Observation | Decision | Strategy |
|---|---|---|---|---|---|---|
| 01:00 | Test final | Use the real clock. Deliberately stop the bot at minute 14 and let it restart | €18,599, 500 orders, 95.8% on time, **0 of 1,030 requests missed** | The bot rebuilt orders, gigs, and dealer beliefs from history and its journal | Restart passed | S7 |
| 01:34–09:30 | Overnight | Baseline plus 24 changes, one at a time, on new `night-N` weeks | Baseline **17,702 ± 386 across 117 weeks**, 95.7% on time | Three main ideas held up out of sample, as shown in the next three rows | | |
| | | `reserve=0` | −809 ± 121 | The driver margin floor held up | Confirmed | S5 |
| | | `late_fee=0` | −453 ± 68 | Resetting the fee after the last pickup held up | Confirmed | S6 |
| | | `calm_eur=300` | −149 ± 70 | The lower cap on the price of lateness in fee selection held up | Confirmed | S2 |
| | | `outage=0` | −59 ± 94 | No measurable benefit from the special outage rule. The price learner adapted during the outage | Record as a limitation | S1 |
| | | `morning=true` | +133 ± 107 (69 weeks) → **+181 ± 84 (115 weeks)**. The worst week improved from 90.0% to 91.6% | Reposting waiting gigs each morning notified that day's drivers | **Enable** (Sunday morning) | S7 |
| | | `on_time=0.95` | +157 ± 113, with 3 weeks below 91% | Small gain with a high risk of going unranked | Drop | S3 |
| | | `reserve=0.15`, `reserve_tight` 1 / 2 | +14, −346 / −222 | No early signal for weeks with scarce driver capacity | Drop | S5 |
| | | `pair_hold=60` | +114, with 1 week unranked | | Drop | S4 |
| | | `look_h=3`, `pair_max_h=7`, `urgent_fee=1.8`, drop the 0.7 fee tier | −649, −303, −125, −258 | | Drop | S2, S4 |

**Phase 5 lesson.** The 8 tuning weeks yielded 17,704 and the 117 new weeks yielded 17,702, with no sign of overfitting.

---

## Phase 6 · Sunday morning analysis of the worst and richest weeks

| Time | Run | Method | Result | Observation | Decision | Strategy |
|---|---|---|---|---|---|---|
| 06:30–07:00 | Analysis | Inspect `night-30` (90.0%) | One dealer sent 18 cars from Joensuu to Oulu in one morning. One car found a driver in time | The problem traced to one batch of cars | | S7 |
| 07:00 | Analysis | Test 9 load features on 16 + 5 weeks | Log loss held at 0.1466, \|z\| < 1.5 | No general pattern | Leave the model as is | S2 |
| 10:24 | Sunday 03:00 ranking round | Build `c4a795fb`, default settings | 16,830 / 15,967 / 10,992 / 17,532 / 17,995 = **€79,317** | In week 4, the rest of the board earned €19–21k and we earned €17.5k | Analyze week 4 | |
| 10:52 | Sweep | `backup=1.26` (shift the normal demand curve up 26% on the competitor's outage day) | +74 ± 114 (60 weeks) | Better fit with little profit impact | Drop | S1 |
| 10:52 | Sweep | `lane_cap=8` (stop accepting cars when 8 of ours are waiting on the same lane of at least 200 km) | Only 3/60 weeks changed. `night-30` gained **1,464 and rose from 90.0% to 91.4% on time**. The other two lost 173 and 120 | Low-cost safeguard | **Enable** | S7 |
| 11:00 | Analysis | Inspect week 4 by day | Won 62% and 58% of requests on Monday and Tuesday, with 30 cars late. On Wednesday the price of a late order rose to €2,463–4,800 and the bot declined 41% of requests | The bot held back for two days. The full week finished at 93.4% on time | Try `ease` | S3 |
| 11:00 | Sweep | Locked build `tag=final` (`morning` + `lane_cap`) on 60 weeks | *Running* | | | S7 |
| 11:20 | Sweep | `ease=0.01` with a cap of `ease_top=0.06`. After a bad day, charge for risk only on cars more likely to be late than the week's current late rate | *Running* | Local replay of week 4 lowered Wednesday–Friday quotes from 1.42–1.60 × to 1.27–1.36 × | *Await results* | S3 |

---

## Ranking rounds (five shared secret weeks)

| Round (Helsinki time) | Build | Per-week margins | Total | Rank | Notes |
|---|---|---|---|---|---|
| Saturday 18:00 | v4.9e or f | | €82,454 | 3 / 67 | 1st place earned €94,445 |
| Saturday 21:00 | v4.9h | 19,345 / 20,581 / 18,801 / 20,537 / 17,586 | €96,850 | 2 / 55 | 1st place earned €105,424. We were weak in weeks 2 and 4 |
| Sunday 03:00 | v4.9k defaults | 16,830 / 15,967 / 10,992 / 17,532 / 17,995 | €79,317 | About 5 / 48 | 1st place earned €88,416. The organizers' best system earned €56,128 |
| Sunday 06:00 | Locked build | *Pending* | | | Dress rehearsal for the final |

---

## Offline analysis of saved weeks

| Question | Data | Observation | Follow-up |
|---|---|---|---|
| How well does the demand curve fit? | 17,999 randomized quotes across 21 weeks | At 42.0% predicted, 39.9% accepted. At 82.7% predicted, 81.7% accepted. Slope 16 fit best (log loss of 0.2964 versus 0.3025 at 12) | Dealer behavior alone fails to explain the gains from a flatter curve. See S5 |
| Is the price learner missing any components? | Add 9 components (dealer × day, car type, hour, etc.) | None reduced log loss | Stop expanding S1 |
| Does the competitor respond? | Exploration weeks | A dealer's price level was about 1.6% lower the day after we won ≥ 30% of their requests | Too small to use |
| Which cars find drivers too late? | 24 weeks | 15.1 cars per week found drivers after their last pickup. All were late and paid 1.6 × typical | S6 |
| Should we offer gigs directly to drivers? | Separate team experiment | The data for this test were unavailable in the repository | Leave out of the final build |
| Did the new build change behavior unexpectedly? | Replay saved weeks through both builds and compare each action | All 2,503 / 2,510 / 2,370 actions matched with the toggle off | Run this check on every new build |

---

## Decision rules used throughout the challenge

1. Make one change at a time and put it behind a toggle that defaults to off.
2. Compare the same weeks. The same seed produces the same week down to the euro.
3. Enable a change when the gain is ≥ max(€250, 1.5 × standard error) and it adds no weeks below 91% on time.
4. Tune on 8 weeks and confirm the results on unseen weeks.

**One exception.** We enabled `morning=true` at +€181, below the €250 threshold. We flagged it after 69 weeks (+€133), and the 46 additional weeks yielded about +€250, repeating the gain on new data. It also raised the worst week from 90.0% to 91.6% on time.
