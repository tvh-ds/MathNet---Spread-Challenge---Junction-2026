# Spread pitch notes and slide guide

This guide covers the judging criteria, the content for each slide, sample scripts, presentation guidelines, and likely questions.

Slide copy and speaker scripts are ready to use. The accompanying notes explain how to build and present the deck.

Fill in each `[__]` placeholder after the final or once the corresponding experiment finishes.

---

## 1. Judging criteria

Once a team reaches the top 10, margin stops counting and the jury uses four criteria.

| Criterion | What the rules say | How we address it |
|---|---|---|
| Elegant | "A simple idea that does a lot of the work. Few parts, each with a reason that you can state." | One sentence explains the approach. *A car costs its fee, plus its risk, plus the driver it takes.* Three formulas and four components. |
| Clear | "We can follow how your system decides... You can explain each of your big ideas and why you had it." | A five-step diagram from request to gig. For each idea, show the observation, the change, and the result. |
| Creative | "An idea that we did not expect: a new way to see the dealers, the drivers or the week." | (a) Drivers are the scarce resource. (b) Stop paying the urgent fee when a car is certain to be late. (c) Put a price on the 90% minimum. |
| Robust | "It does well on weeks it has never seen, and you show this with results over many weeks. It survives a restart, a slow network and a surprise." | Show 117 unseen weeks, the deliberate interruption during the test final, and the week that finished at 90.0% on time. |

The rules require three things for **each major idea**.

1. **The idea.** Explain what the system does and when.
2. **Why.** Explain which observation or result prompted the idea.
3. **The effect.** Compare margin **and** the on-time rate on the same weeks with the idea enabled and disabled.

Include the final result, best ranking round, ideas that failed, and conditions that would break the system.

The rules ask the whole team to take this instruction seriously.

> "If an agent wrote your slides, read every line and cut each one that you cannot explain yourself."

Remove every line the presenter cannot explain. Review Section 2 as a team before building the slides.

---

## 2. Three formulas to explain

### 2.1 Quotes for dealers

$$
p^{*} = \arg\max_{p}\; \big(p - c\,(1+r)\big)\cdot P(\text{yes}\mid p)
$$

- $p$ is the dealer quote, expressed as a multiple of list price.
- $c$ is the car's expected cost (Section 2.2).
- $r = 0.10$ is the markup, called the price of a driver.
- $P(\text{yes}\mid p)$ is the probability that the dealer accepts, learned during the week.

A car with an expected cost of €100 has a floor of €110. Decline the order if the dealer will pay at most €105.

### 2.2 The cost of a car

$$
c = \mathbb{E}[\text{fee paid}] + P(\text{late})\cdot \text{refund} + \big(P(\text{late}) - 4\%\big)\cdot \lambda
$$

- $\mathbb{E}[\text{fee paid}]$ is the final driver fee predicted by the model.
- $P(\text{late})$ is the model's predicted probability of late delivery.
- The refund goes to the dealer for a late delivery (10–25% if delivered the same day, 50% if 1–3 days late).
- $\lambda$ is the price of a late order. It rises as the week uses more of its 4% lateness allowance, up to about €300.

A car with a 10% chance of arriving late is 6 percentage points above the allowance. With $\lambda$ at €150, that adds 0.06 × 150 = €9 to the cost. A safer car with a 2% chance of being late gets a discount of 0.02 × 150 = €3.

### 2.3 The fee for a gig

$$
f^{*} = \arg\min_{f}\; \mathbb{E}[\text{fee paid}\mid f] + P(\text{late}\mid f)\cdot L
$$

- $f$ is the opening fee, set at one of six levels (0.70 / 0.85 / 1.00 / 1.15 / 1.30 / 1.50 × the typical fee).
- $L$ is the loss from a late delivery. It includes the refund, the dealer's trust, and $\lambda$, with a €150 cap in the fee calculation.

Opening at 0.70 × typical yielded 87.4% on time. Opening at 1.00 × yielded 97.4%. For a car with a €50 typical fee and $L$ at €100, spending €15 to reduce lateness by 10 percentage points buys €10 of expected benefit. At €200, the same improvement is worth €20. Higher-value, higher-risk cars can justify higher fees.

---

## 3. Slide content (9 slides, 10 maximum)

Make **one claim per slide** and show the evidence for it. Use a full sentence with a number as the title.

### Slide 1 · Lead with the result

**Title** `Price what a car really costs: €[__] in the final`

**Slide copy**

- Final: `€[__] margin, [__]% on time, place [__] of [__]`
- Best ranking round: `€96,850 for five secret weeks, place 2 of 55 ranked teams (Saturday 21:00)`
- Latest round: `€79,317 for five secret weeks (Sunday 03:00), against €56,128 for the organizers' best system and −€362,463 for their starter kit`
- Practice: `€17,702 a week on 117 level-8 weeks the desk had never played (± 386). All 117 ranked, 95.7% of orders on time.`
- Give each of the three ideas one line with its measured effect.
  - `A car costs more than its fee: +€809 a week (± 121)`
  - `Late is late: +€453 a week (± 68)`
  - `One fee per gig, from a model of our own weeks: +€1,400 a week`

**Speaker script (20 seconds)**
"Our desk earned [__] euros in the final. It runs on one idea: a car costs more than the fee we pay its driver. It costs the fee, the risk that it arrives late, and the driver it takes from our other cars. Three ideas follow from that, and we measured each one on the same weeks."

The rules say "Start with the answer." Put the results before team introductions.

---

### Slide 2 · How the system decides

**Title** `From a request to a delivered car in five steps`

Use a five-box diagram connected by arrows. Draw the decision flow directly.

1. `Cost` — fee we expect to pay + refund × P(late) + the car's use of the room under the 90% minimum
2. `Floor` — cost × 1.10 (the driver this car takes)
3. `Price` — the multiple of list price where (price − floor) × P(yes) is largest
4. `Menu` — every option the car can make, each at the same margin
5. `Gig` — one fee from the model; a second car joins when it starts where the first ends

Below the diagram, add this line. `The 90% minimum is a price too: the more of its 4% of late orders a week has used, the more a risky car costs.`

**Speaker script (30 seconds)**
"A request arrives. We compute what the car will cost us: the fee, plus the refund times the chance it is late. We add ten percent for the driver it takes. Then we quote the price that maximises expected margin, given what this week's dealers have accepted so far. We quote every option at the same margin, so the dealer picks the speed. When we win, the gig opens at the one fee where fee plus risk is smallest."

This slide addresses "Clear." The jury should be able to follow the logic from the diagram.

---

### Slide 3 · Idea 1. A car costs more than its fee

**Title** `A car costs more than its fee: it takes a driver. +€809 a week`

**The idea:** `Every order must earn 10% above its expected cost. Fewer orders, each one paid for.`

**Why:** `A flatter demand curve earned more money. Yet 17,999 random quotes fit the steep curve better. So the dealers were not the reason: each order we won made our waiting cars later and dearer.`

**The effect** (same 8 weeks, one setting changed)

| Margin floor above cost | € a week | Orders | On time |
|---|---|---|---|
| 0% | 16,415 | 527 | 95.2% |
| **10% (ours)** | **17,578** | 483 | 96.0% |
| 20% | 17,317 | 425 | 95.7% |
| 30% | 15,837 | 358 | 96.6% |

Below the table, add this line. `On 117 weeks the desk had never played: €17,702 a week with it, €16,893 without (+€809 ± 121). On time 95.7% against 95.1%.`

**Speaker script (35 seconds)**
"This is the idea we did not expect. We fitted the dealers' demand curve on eighteen thousand random quotes. A wrong, flatter curve earned more. That made no sense, until we saw that the scarce side is drivers, not dealers. Every order takes a driver that our waiting cars do not get. So we charge for it: ten percent on top of cost. We win forty-four fewer orders a week, earn eight hundred euros more on weeks we had never played, and more cars arrive on time."

This slide makes the strongest case for "Creative." Present the paradox first, then the explanation and the result.

---

### Slide 4 · Idea 2. Late is late

**Title** `Late is late: a car that cannot be on time stops bidding for drivers. +€453 a week`

**The idea:** `Once a car's last pickup has passed with no driver, its gig starts again at the typical fee, and climbs one step every four working hours. Before: it stayed at the urgent fee, 1.6 × typical.`

**Why** (cars without a driver at the deadline warning)

| Driver booked with | Cars a week | Late | Fee paid |
|---|---|---|---|
| over 150 minutes left | 7.5 | 24% | 1.6 × |
| 60 to 150 minutes left | 5.1 | 8% | 1.6 × |
| under 60 minutes left | 0.4 | 30% | 1.6 × |
| **last pickup already past** | **15.1** | **100%** | **1.6 ×** |

**The effect:** `€15,551 → €16,415 a week (+€864, better on 8 of 8 weeks), on time 94.6% → 95.2%. On 115 unseen weeks: €17,186 without it, +€453 (± 68), on time unchanged at 95.8%.`

**Speaker script (25 seconds)**
"Fifteen cars a week found their driver after their last pickup. Every one arrived late, and every one paid the urgent fee, sixty percent above typical. That money bought nothing, and it pulled drivers away from cars that could still be on time. Now such a car goes back to the typical fee. Margin went up, and so did the on-time share."

---

### Slide 5 · Idea 3. Use a model to choose one fee per gig

**Title** `One fee per gig, where the fee and the risk of a late car cost least`

**The idea:** `For each car: the fee step where (fee we expect to pay) + P(late) × (cost of a late car) is smallest. One step up after six working hours, again 8 and 5 hours before the last pickup.`

**Why** (16 weeks with randomized opening fees, 7,235 cars)

| Opening fee, × typical | On time | Paid in the end |
|---|---|---|
| 0.70 | 87.4% | 0.95 × |
| 0.85 | 92.6% | 0.98 × |
| **1.00** | **97.4%** | **1.05 ×** |
| 1.15 | 97.5% | 1.18 × |
| 1.30 | 98.0% | 1.32 × |
| 1.50 | 98.1% | 1.50 × |

Close with this line. `The typical fee is a threshold. Under it, cars wait and arrive late. Over it, we only pay more.`

**The effect:** `€12,172 → €13,572 a week when the model replaced fixed fee steps, same 8 weeks. Capping the price of lateness inside the fee choice: +€149 a week (± 70) on 115 unseen weeks.`

**Speaker script (25 seconds)**
"We played sixteen weeks where each gig opened at a random fee. The result is a threshold: below the typical fee, cars arrive late; above it, we just pay more. So the desk picks, for each car, the fee where fee plus risk is smallest. A long lane with a tight deadline gets more. A short lane with three days gets less."

---

### Slide 6 · Idea 4. Dealers

**Title** `Dealers: one price level, learned during the week, and a menu at one margin`

**The idea:**
- `P(yes) is a logistic curve around a price level. The level is a sum: the week, the day, the dealer, the two towns, and 1% for each order we delivered to that dealer on time. Each answer moves every part it touched.`
- `We quote every option at the same margin: a slower option is worth €15, then €8 less to the dealer.`

**Why** (17,999 randomized quotes, with forecasts made before the dealer's response)

| Our price against the learned level | Forecast yes | Actual yes |
|---|---|---|
| 10 to 15% above | 17.3% | 16.3% |
| 0 to 5% above | 42.0% | 39.9% |
| 0 to 5% below | 57.7% | 59.1% |
| 10 to 15% below | 82.7% | 81.7% |

**The effect:** `Euro gaps between options and lanes: €13,572 → €14,740 a week. One option instead of the menu: [€__].`

**Outage rule note (small type)** `A separate rule for the competitor's outage day earned nothing we could measure: −€59 a week (± 94) without it, on 115 weeks. The learner follows that day by itself.`

**Speaker script (25 seconds)**
"On the dealer side, the desk learns one number during the week: the price level at which this dealer says yes half the time. Every answer updates it. The forecast is calibrated: when it says forty-two percent, we win forty percent. And we let the dealer choose the speed: every option is quoted at the same margin."

---

### Slide 7 · Idea 5. Two cars, one driver

**Title** `Two cars, one driver: a new car joins a waiting car when it starts where the other ends`

**The idea:** `Two cars share one gig when the second starts within 30 km of where the first ends, the drive is under five hours, and both cars are ready in time. The gig pays 0.75 × the two typical fees.`

**Why:** `A driver who delivers far from home has to travel back anyway. A car that goes the same way pays for that trip.`

**The effect:**
- `14 to 21% of cars travel in a two-car gig`
- `0.80 to 0.83 × the typical fee per car, against 0.94 to 0.99 × for a car alone`
- `Without pairs, same weeks: [€__ a week, __% on time]`

**Callout for the bug the data revealed** `17 gigs paired a car that was not ready yet with a car due earlier. 18 cars arrived 14 to 89 hours late. One check now refuses such pairs: +€811 a week.`

**Speaker script (20 seconds)**
"When a new car starts where a waiting car ends, one driver takes both, for three quarters of the two fees. The data also showed us a bug: we paired cars that were not ready yet. Eighteen cars arrived days late. One line fixed it, and that line was worth eight hundred euros a week."

---

### Slide 8 · Robustness and validation

**Title** `The same weeks, one change at a time: €17,702 on 117 weeks it had never seen`

**Slide copy (four boxes)**

1. **Paired weeks.** `A seed gives the same week to the euro. On the same seeds, every difference is the change itself.`
2. **Unseen weeks.** `Tuned on 8 weeks: €17,704 a week. Played once on 117 new weeks: €17,702. All 117 ranked.`
3. **A night of tests, and one change taken.** `24 changes, one at a time, on 115 weeks. One was taken: gigs left from an earlier day are posted again each working morning, +€181 a week (± 84), and the worst week rose from 90.0% to 91.6% on time.`
4. **A restart and a live clock.** `Test final with a stop on purpose: €18,599, 95.8% on time, 0 of 1,030 requests missed. The desk rebuilds its books from the world's history and its own journal.`

Use a seven-bar chart (12,172 → 13,572 → 14,740 → 15,551 → 16,415 → 17,578 → 17,704) with a zero baseline.

**Speaker script (30 seconds)**
"How do we know? The world repeats: the same seed gives the same week to the euro. So every comparison is on the same weeks with one change. We tuned on eight weeks, then played one hundred and seventeen new ones once. Seventeen thousand seven hundred and four euros became seventeen thousand seven hundred and two. All of them were ranked. And we stopped the desk on purpose during a test final: it came back and missed no request."

---

### Slide 9 · Limitations

**Title** `What did not work, what would break it, and what we do not know`

**Column 1 · Did not work (€ per week, same weeks)**
- `A margin floor that follows the queue: −380 to −820`
- `Cheaper early orders to build a dealer's trust: −381`
- `On-time target 95% instead of 96%: +157, but 3 weeks under 91%`
- `Urgent fee 1.4 × instead of 1.6 ×: −505`
- `Nine more parts in the dealer model: no better forecast`

**Column 2 · Would break it**
- `One dealer's batch for a far town. 18 cars from Joensuu to Oulu found 1 driver in time. That week, 1 of 117, ended at exactly 90.0% on time. No general sign explained it, so a cap now refuses a car when 8 of ours already wait on the same long lane: that week ends at 91.4%.`
- `A week whose drivers are far from the 37 weeks we fitted: the fee model extrapolates.`
- `Minutes of downtime: the journal restores the desk, not the quotes it missed.`

**Column 3 · Open questions**
- `In weeks where every team earns most, we earned less than teams we beat overall (Sunday 03:00, week 4: €17,532 against €19,000 to €22,400). We found the cause on Sunday morning: after two days with 30 late cars, our own price of a late order rose from under €100 to €2,463, and the desk declined 41% of Wednesday's requests.` [ADD ONE SENTENCE ABOUT `ease` WHEN THE TEST RESULTS ARE AVAILABLE]
- `Slope 12 earns more than the best-fitting 16. With the margin floor in the cost, we no longer know why.`

**Slide footer · Sources and credits** `Our practice runs tested driver capacity, fee timing, and pickup readiness for paired gigs. We also tested direct offers and left them out. The dealer-note reader is used under the MIT licence. Claude wrote most of the code and analysis. We chose what to test and what to keep.` [Experiment log](../research/EXPERIMENT_LOG.md) · [Dealer-note reader license](../../engine/notes_reader.py)

**Speaker script (25 seconds)**
"Three honest limits. First, one week in a hundred and seventeen ended at exactly ninety percent: one dealer sent eighteen cars to one far town, and one found a driver in time. We looked for a general rule and found none, so we added a simple cap. Second, in the richest weeks, teams we beat overall earned more than we did. This morning we found why: after two bad days, our own price of lateness made the desk decline four requests in ten. Third, a flatter demand curve still earns more than the true one, and we cannot fully explain it."

The rules say "A team that shows its limits is easier to trust." If time is short, cut slide 6 or 7 first and keep this one.

---

## 4. Slide design guide

### 4.1 Presentation rules from "Say it clearly"

| Rule | How to apply it |
|---|---|
| Start with the answer | Put the result and three ideas on slide 1. Skip "About us" and "Agenda" slides. |
| One idea on a slide | Write the title as **a claim with a number**. Use the body to support that claim. |
| Give each figure a unit and a comparison | Write `€17,578 a week, against €16,415 without it, on the same 8 weeks`. |
| Show how it decides | Use formulas, rules, and diagrams. Skip code screenshots. |
| Use the challenge vocabulary | Dealer, request, gig, fee, typical fee, deadline, list price, option. See Section 4.2. |
| Cut what does not help | Leave out slogans, long lists, and decorative logos. |
| Say what did not work | Slide 9. |

### 4.2 Terminology

| Avoid | Use |
|---|---|
| reserve, shadow price, congestion price | `a margin floor of 10% above the car's cost`. Once defined, this can be called *the price of a driver*. |
| late_fee, calm_eur, lane_cap (parameter names) | Describe the behavior in words, for example `the fee of a car past its last pickup`. |
| customer, client | `dealer` |
| job, task, trip | `gig` |
| reference fee, base fee | `typical fee` |
| tuning set / test set | `the 8 weeks we tuned on` / `117 weeks the desk had never played` |
| SLA, service level | `on-time share`, `the 90% delivery minimum` |

### 4.3 Layout

- Use a 16:9 layout, wide margins, and one accent color for the "ours" row and the measured effect.
- Set titles at ≥ 36 pt, body text at ≥ 20 pt, and source notes at ≥ 14 pt.
- Use the same three blocks on each idea slide. Put **What we saw** at the top left, **What the desk does** at the bottom left, and the chart or table with the measured effect on the right.
- Use at most one table or visual per slide and at most six rows per table.
- Use a source line at the foot of the slide. `Level 8, seeds halal-09 to halal-16, the same 8 weeks. ± is one standard error of the paired difference.`
- Start bar charts at zero.

### 4.4 What to cut when time is short

1. Combine slide 7 (pairing) and slide 6 into "Dealers and pairs."
2. Replace the calibration table on slide 6 with one sentence.
3. **Keep slides 1, 2, 3, 8, and 9.**

### 4.5 Submission checklist

- [ ] Each figure has a unit and a comparison.
- [ ] Every figure can be traced to `sweeps.jsonl`, `board.py`, or the experiment log.
- [ ] Fill in every `[__]` placeholder.
- [ ] The presenter reads each line aloud and removes any line they cannot explain.
- [ ] Include 5 to 10 slides.
- [ ] Export a PDF and check the fonts on another computer.
- [ ] Submit the hash from the team page, the slides, and the public code link. Check the link in a private browser window.

---

## 5. Speaker scripts

### 5.1 60-second version

"Our desk runs on one idea: a car costs more than the fee we pay its driver. It costs the fee, the risk of arriving late, and the driver it takes from our other cars.

We found this through a paradox. A wrong demand curve earned more than the right one. The reason was that drivers, not dealers, are the scarce side. So every order must earn ten percent above its cost. That alone is worth eight hundred euros a week.

The second idea: a car that can no longer be on time stops paying the urgent fee. The third: each gig gets the one fee where fee plus risk is smallest, from a model of our own weeks.

We tuned on eight weeks and then played one hundred and seventeen new ones once: seventeen thousand seven hundred euros a week, all ranked. In the final we earned [__]."

### 5.2 Four-minute version

Read the speaker scripts for slides 1 through 9 in Section 3. The total is about 235 seconds.

### 5.3 Suggested assignments for four presenters

| Presenter | Slides | Preparation |
|---|---|---|
| A (opening and closing) | 1, 2, 9 | The three formulas in Section 2 and the three limitations |
| B (drivers) | 3, 4, 5 | The three tables, the reason for 10%, and why the fee goes to 1.6 × and then back to 1.0 × |
| C (dealers and pairing) | 6, 7 | How the price level is learned, the pairing conditions, and the pairing bug |
| D (evidence) | 8 and code questions | Paired comparisons, 117 weeks, restart behavior, and repository structure |

If one person presents, they should read Sections 2 and 6 three times.

---

## 6. Likely jury questions

**"Why 10%?"**
"We measured it. On the same 8 weeks: 0% gives €16,415, 10% gives €17,578, 20% gives €17,317, 30% gives €15,837. The top is near 10 to 13%. We also tried making it follow the queue or the week. Both lost money, so it is a constant."

**"How do you know you did not overfit to your 8 weeks?"**
"We played 117 new weeks once. €17,704 a week on the 8 weeks we tuned on, €17,702 on the 117. Each of the three ideas held there: +809, +453 and +149 euros a week. The first two are more than six standard errors from zero."

**"What happens if your system stops during the final?"**
"We start it again. It rebuilds orders and gigs from the world's history, and its beliefs about dealers from a journal it writes as it plays. We tested it in a test final with a stop on purpose: no request was missed, and beliefs matched to zero."

**"How does the 90% minimum enter your decisions?"**
"As a price, not a rule. Each car's cost includes its chance of being late times a price. That price is near zero while we expect far fewer late orders than the 4% we allow ourselves, and it rises steeply near that share. A safe car earns room back."

**"Which requests do you decline?"**
"Three kinds. A car that no driver can collect in time. An order with two cars. And any car whose cost plus 10% is above what this week's dealers pay."

**"Why does a wrong demand curve earn more?"**
"A flatter curve asks for more margin an order, so it wins fewer orders, and that helps when drivers are scarce. Once we put the driver's price into the cost, most of that gain went away. A part remains that we cannot explain."

**"What surprised you most?"**
"Two things. That lowering the fee of our most overdue cars raised both margin and on-time share. And one week where a single dealer sent 18 cars to one far town on a Friday: one found a driver in time."

**"What would you do with one more week?"**
"The richest weeks. Our price of lateness looks only backwards: it lets the desk spend a whole week's allowance of late cars on Monday, and then stops it selling on Wednesday. It should look forward over the week."

**"Did you use reinforcement learning?"**
"No. A week takes about 40 seconds and we could play a few hundred. So we fitted two small models on weeks with random prices and fees, and each decision is an optimisation on those models. The dealer's price level is learned inside the week with a Bayesian update."

**"What did the AI do, and what did you do?"**
"Claude wrote most of the code and the analysis. We decided what to test, set the decision rule before each test, and chose what to keep. Most ideas were rejected, and we can explain each one that stayed."

**"How do you set the fee of a gig over time?"**
"One fee when it opens. One step up after six working hours without a driver, and again 8 and 5 working hours before the last pickup. At the deadline warning, 1.6 × typical. After the last pickup has passed, back to 1.0 ×."

**"When do you combine cars?"**
"When a new car starts within 30 km of where a waiting car ends, the planned drive is under five hours, and neither car is collected before it is ready. Not on Fridays. If no driver takes the pair within 45 minutes, the cars go alone."

---

## 7. Where to find the missing figures

| Missing figure | Source |
|---|---|
| Final result | The `End` line in `final.log` and the final leaderboard |
| Menu disabled and pairing disabled | `python sweep.py --summary tag=deck`, if the runs finish in time |
| Ranked teams in the Sunday 03:00 round | `python board.py` |
