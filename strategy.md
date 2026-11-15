# Final dispatch strategies

The [final launcher](engine/final.sh) uses the defaults in [dispatch.py](engine/dispatch.py) and the fitted parameters in [model.json](engine/model.json). The ranking uses average margin gain per level-8 practice week, using the eight-week tuning result where available. Each paired comparison has its own baseline. ± denotes one standard error.

| Rank | Strategy | Margin gain per week | Impact |
|---:|---|---:|---|
| 1 | **Model-selected opening fee.** Choose the fee that minimizes expected payout plus lateness cost. Raise it as working time runs out. | **+€1,400** on 8 tuning weeks | In randomized fee trials, 0.70× typical yielded 87.4% on time and 1.00× yielded 97.4%. Higher fees brought little further improvement. |
| 2 | **Adaptive dealer pricing and delivery menu.** Learn from each response, account for town and dealer effects, and quote feasible speeds at a common margin using fixed euro gaps. | **+€1,168** on 8 tuning weeks for the fixed gaps and route-level pricing | Dealers choose the speed. The weekly gain measures the pricing change, with a separate menu-only result pending in the experiment records. |
| 3 | **10% margin floor above expected cost.** Price in the driver a new order takes from the queue. | **+€1,163** on 8 tuning weeks | Won all 8 comparisons. On 117 unseen weeks, **+€809 ± €121** and on-time delivery rose from 95.1% to 95.7%. |
| 4 | **Reset the fee after the last pickup.** Drop from 1.6× urgent to 1.0× typical once on-time delivery is impossible. | **+€864** on 8 tuning weeks | On-time delivery rose from 94.6% to 95.2% in tuning. On 115 unseen weeks, **+€453 ± €68** with the same on-time rate. |
| 5 | **Pair compatible cars and check pickup readiness.** Use one driver when the second pickup is near the first drop-off and both cars fit their windows. Split unbooked pairs after 45 minutes. | **+€811** on 8 tuning weeks for the readiness check | Pairing itself gained €699 in a separate two-week trial, with on-time delivery falling from 97.1% to 96.5%. The readiness check addresses pairs that left cars 14–89 hours late. |
| 6 | **Repost waiting gigs each working morning.** Notify that day's drivers about jobs carried over from earlier days. | **+€181 ± €84** on 115 unseen weeks | Worst week improved from 90.0% to 91.6% on time. |
| 7 | **Cap the lateness premium at €150 when choosing fees.** Keep the full risk price available when deciding which orders to take. | **+€126** on 8 tuning weeks | **+€149 ± €70** on 115 unseen weeks. Higher fees mainly moved drivers between our gigs. |
| 8 | **Cap long-lane backlog.** Allow up to eight waiting cars on a lane of at least 200 km. | **About +€20** across 60 test weeks | Changed three weeks. The weakest gained €1,464 and rose from 90.0% to 91.4% on time. The other two lost €173 and €120. |

## Qualification and reliability

- **Price the risk of missing the 90% cutoff.** Target 96% on time and increase the cost of risky quotes as expected late orders approach the 4% allowance. A 90% target finished at 89.5% and went unranked in the recorded trial.
- **Recover after a restart.** Relaunch after three seconds and rebuild from event history and the local journal. In the test final with a deliberate stop, the bot missed 0 of 1,030 requests and delivered 95.8% of orders on time.
- **Use dealer notes and repost urgent gigs.** Apply pickup readiness and site constraints, and post a fresh gig when a fee increase or a lost driver makes timing critical.
- **Adapt quotes to competitor outages.** The enabled outage rule's estimate was +€59 ± €94 per week, within one standard error of zero.

Measurements and test baselines are recorded in the [experiment log](docs/research/EXPERIMENT_LOG.md) and [README](README.md).
