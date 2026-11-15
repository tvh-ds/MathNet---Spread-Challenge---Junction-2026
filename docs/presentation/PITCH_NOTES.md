# MathNet1 · Spread: key notes thuyết trình và hướng dẫn làm slides

Bản này KHÔNG phải slides. Nó là: (1) giám khảo muốn thấy gì, (2) nội dung từng slide để team tự dựng, (3) lời nói mẫu, (4) hướng dẫn trình bày, (5) câu hỏi dễ gặp.

Quy ước: phần **chữ trên slide** và **lời nói** viết bằng tiếng Anh (dùng được ngay). Phần giải thích cho team viết bằng tiếng Việt.

Ô `[__]` = số chưa có, điền sau final hoặc sau khi chạy xong bài thử.

---

## 1. Giám khảo chấm gì (đọc từ quy chế)

Sau khi vào top 10, **margin không còn được tính**. Giám khảo chấm 4 thứ:

| Tiêu chí | Quy chế viết | Ta trả lời bằng gì |
|---|---|---|
| Elegant | "A simple idea that does a lot of the work. Few parts, each with a reason that you can state." | Một câu: *a car costs its fee, plus its risk, plus the driver it takes.* Ba công thức, bốn bộ phận. |
| Clear | "We can follow how your system decides... You can explain each of your big ideas and why you had it." | Một sơ đồ 5 bước từ request đến gig. Mỗi ý có "thấy gì → làm gì → được gì". |
| Creative | "An idea that we did not expect: a new way to see the dealers, the drivers or the week." | (a) Bên khan hiếm là tài xế, không phải đại lý. (b) Xe đã chắc chắn trễ thì ngừng trả phí khẩn. (c) Mức 90% là một cái giá, không phải luật. |
| Robust | "It does well on weeks it has never seen, and you show this with results over many weeks. It survives a restart, a slow network and a surprise." | 117 tuần chưa từng chơi; thử tắt giữa chừng ở test final; kể thật về tuần 90,0%. |

Với **mỗi ý lớn**, quy chế đòi đúng 3 thứ:

1. **The idea**: hệ thống làm gì, trong trường hợp nào.
2. **Why**: thấy gì trong thế giới hoặc trong kết quả mà nảy ra ý đó.
3. **The effect**: margin **và** tỷ lệ đúng hạn, có và không có ý đó, trên cùng các tuần.

Ngoài ra bắt buộc có: kết quả final, vòng xếp hạng tốt nhất, cái gì không hiệu quả, cái gì làm hỏng hệ thống.

Một câu trong quy chế cần cả team đọc kỹ:

> "If an agent wrote your slides, read every line and cut each one that you cannot explain yourself."

Nghĩa là: dòng nào trên slide mà người thuyết trình không tự giải thích được thì **xoá**. Mục 2 dưới đây là để cả team hiểu trước khi dựng slide.

---

## 2. Ba công thức phải hiểu (để tự giải thích được)

### 2.1 Giá báo cho đại lý

$$
p^{*} = \arg\max_{p}\; \big(p - c\,(1+r)\big)\cdot P(\text{yes}\mid p)
$$

- $p$: giá báo cho dealer (bội số của list price)
- $c$: chi phí kỳ vọng của xe (mục 2.2)
- $r = 0{,}10$: phần cộng thêm, "giá của một tài xế"
- $P(\text{yes}\mid p)$: xác suất dealer đồng ý, học trong tuần

Ví dụ: xe có $c$ = €100. Sàn = €110. Nếu dealer chỉ chịu trả tối đa €105 thì ta không lấy đơn này.

### 2.2 Chi phí của một xe

$$
c = \mathbb{E}[\text{fee paid}] + P(\text{late})\cdot \text{refund} + \big(P(\text{late}) - 4\%\big)\cdot \lambda
$$

- $\mathbb{E}[\text{fee paid}]$: phí cuối cùng ta trả tài xế, do mô hình dự đoán
- $P(\text{late})$: xác suất xe trễ, do mô hình dự đoán
- refund: tiền hoàn cho dealer khi trễ (10–25% nếu trễ trong ngày, 50% nếu trễ 1–3 ngày)
- $\lambda$: "giá của một đơn trễ". Tuần càng dùng gần hết 4% xe được phép trễ thì $\lambda$ càng cao (tối đa khoảng €300)

Ví dụ: xe có 10% khả năng trễ, vượt mức cho phép 6 điểm. Với $\lambda$ = €150 thì phần này cộng thêm 0,06 × 150 = €9 vào chi phí. Xe an toàn (2% trễ) thì được trừ đi 0,02 × 150 = €3.

### 2.3 Phí của một gig

$$
f^{*} = \arg\min_{f}\; \mathbb{E}[\text{fee paid}\mid f] + P(\text{late}\mid f)\cdot L
$$

- $f$: phí mở đầu, là một trong 6 mức 0,70 / 0,85 / 1,00 / 1,15 / 1,30 / 1,50 × typical fee
- $L$: thiệt hại nếu xe trễ (refund + lòng tin của dealer + $\lambda$, tối đa €150 trong phép chọn phí)

Ví dụ: mở ở 0,70 × thì 87,4% xe đúng hạn; mở ở 1,00 × thì 97,4%. Với xe có typical fee €50 và $L$ = €100: trả thêm €15 để bớt 10 điểm trễ (đáng giá €10)... chưa đáng. Với $L$ = €200 thì đáng. Vì vậy xe rủi ro cao, giá trị cao được phí cao hơn.

---

## 3. Nội dung từng slide (9 slide, tối đa 10)

Mỗi slide: **một khẳng định + bằng chứng của nó.** Tiêu đề là một câu có con số, không phải một chủ đề.

### Slide 1 · Câu trả lời trước

**Tiêu đề:** `Price what a car really costs: €[__] in the final`

**Trên slide:**

- Final: `€[__] margin, [__]% on time, place [__] of [__]`
- Best ranking round: `€96,850 for five secret weeks, place 2 of 55 ranked teams (Saturday 21:00)`
- Latest round: `€79,317 for five secret weeks (Sunday 03:00), against €56,128 for the house's best system and −€362,463 for the house starter`
- Practice: `€17,702 a week on 117 level-8 weeks the desk had never played (± 386). All 117 ranked, 95.7% of orders on time.`
- Ba ý, mỗi ý một dòng kèm hiệu quả:
  - `A car costs more than its fee: +€809 a week (± 121)`
  - `Late is late: +€453 a week (± 68)`
  - `One fee per gig, from a model of our own weeks: +€1,400 a week`

**Lời nói (20 giây):**
"Our desk earned [__] euros in the final. It runs on one idea: a car costs more than the fee we pay its driver. It costs the fee, the risk that it arrives late, and the driver it takes from our other cars. Three ideas follow from that, and we measured each one on the same weeks."

**Ghi chú:** quy chế yêu cầu "Start with the answer". Không mở đầu bằng giới thiệu team.

---

### Slide 2 · Hệ thống quyết định thế nào

**Tiêu đề:** `From a request to a delivered car in five steps`

**Hình:** sơ đồ 5 ô nối bằng mũi tên. Không dùng ảnh chụp code.

1. `Cost` — fee we expect to pay + refund × P(late) + the car's use of the room under the 90% minimum
2. `Floor` — cost × 1.10 (the driver this car takes)
3. `Price` — the multiple of list price where (price − floor) × P(yes) is largest
4. `Menu` — every option the car can make, each at the same margin
5. `Gig` — one fee from the model; a second car joins when it starts where the first ends

Dưới sơ đồ, một dòng: `The 90% minimum is a price too: the more of its 4% of late orders a week has used, the more a risky car costs.`

**Lời nói (30 giây):**
"A request arrives. We compute what the car will cost us: the fee, plus the refund times the chance it is late. We add ten percent for the driver it takes. Then we quote the price that maximises expected margin, given what this week's dealers have accepted so far. We quote every option at the same margin, so the dealer picks the speed. When we win, the gig opens at the one fee where fee plus risk is smallest."

**Ghi chú:** đây là slide "Clear". Giám khảo phải theo được logic mà không cần đọc code.

---

### Slide 3 · Ý 1: một xe tốn hơn phí của nó

**Tiêu đề:** `A car costs more than its fee: it takes a driver. +€809 a week`

**The idea:** `Every order must earn 10% above its expected cost. Fewer orders, each one paid for.`

**Why:** `A flatter demand curve earned more money. Yet 17,999 random quotes fit the steep curve better. So the dealers were not the reason: each order we won made our waiting cars later and dearer.`

**The effect** (bảng, cùng 8 tuần, chỉ đổi một số):

| Margin floor above cost | € a week | Orders | On time |
|---|---|---|---|
| 0% | 16,415 | 527 | 95.2% |
| **10% (ours)** | **17,578** | 483 | 96.0% |
| 20% | 17,317 | 425 | 95.7% |
| 30% | 15,837 | 358 | 96.6% |

Dòng dưới bảng: `On 117 weeks the desk had never played: €17,702 a week with it, €16,893 without (+€809 ± 121). On time 95.7% against 95.1%.`

**Lời nói (35 giây):**
"This is the idea we did not expect. We fitted the dealers' demand curve on eighteen thousand random quotes. A wrong, flatter curve earned more. That made no sense, until we saw that the scarce side is drivers, not dealers. Every order takes a driver that our waiting cars do not get. So we charge for it: ten percent on top of cost. We win forty-four fewer orders a week, earn eight hundred euros more on weeks we had never played, and more cars arrive on time."

**Ghi chú:** đây là slide "Creative" mạnh nhất. Kể đúng thứ tự: nghịch lý → lời giải → số.

---

### Slide 4 · Ý 2: trễ là trễ

**Tiêu đề:** `Late is late: a car that cannot be on time stops bidding for drivers. +€453 a week`

**The idea:** `Once a car's last pickup has passed with no driver, its gig starts again at the typical fee, and climbs one step every four working hours. Before: it stayed at the urgent fee, 1.6 × typical.`

**Why** (bảng, xe đến deadline warning mà chưa có tài xế):

| Driver booked with | Cars a week | Late | Fee paid |
|---|---|---|---|
| over 150 minutes left | 7.5 | 24% | 1.6 × |
| 60 to 150 minutes left | 5.1 | 8% | 1.6 × |
| under 60 minutes left | 0.4 | 30% | 1.6 × |
| **last pickup already past** | **15.1** | **100%** | **1.6 ×** |

**The effect:** `€15,551 → €16,415 a week (+€864, better on 8 of 8 weeks), on time 94.6% → 95.2%. On 115 unseen weeks: €17,186 without it, +€453 (± 68), on time unchanged at 95.8%.`

**Lời nói (25 giây):**
"Fifteen cars a week found their driver after their last pickup. Every one arrived late, and every one paid the urgent fee, sixty percent above typical. That money bought nothing, and it pulled drivers away from cars that could still be on time. Now such a car goes back to the typical fee. Margin went up, and so did the on-time share."

---

### Slide 5 · Ý 3: một mức phí cho mỗi gig, từ mô hình

**Tiêu đề:** `One fee per gig, where the fee and the risk of a late car cost least`

**The idea:** `For each car: the fee step where (fee we expect to pay) + P(late) × (cost of a late car) is smallest. One step up after six working hours, again 8 and 5 hours before the last pickup.`

**Why** (16 tuần với phí mở đầu ngẫu nhiên, 7.235 xe):

| Opening fee, × typical | On time | Paid in the end |
|---|---|---|
| 0.70 | 87.4% | 0.95 × |
| 0.85 | 92.6% | 0.98 × |
| **1.00** | **97.4%** | **1.05 ×** |
| 1.15 | 97.5% | 1.18 × |
| 1.30 | 98.0% | 1.32 × |
| 1.50 | 98.1% | 1.50 × |

Một dòng kết luận: `The typical fee is a threshold. Under it, cars wait and arrive late. Over it, we only pay more.`

**The effect:** `€12,172 → €13,572 a week when the model replaced fixed fee steps, same 8 weeks. Capping the price of lateness inside the fee choice: +€149 a week (± 70) on 115 unseen weeks.`

**Lời nói (25 giây):**
"We played sixteen weeks where each gig opened at a random fee. The result is a threshold: below the typical fee, cars arrive late; above it, we just pay more. So the desk picks, for each car, the fee where fee plus risk is smallest. A long lane with a tight deadline gets more. A short lane with three days gets less."

---

### Slide 6 · Ý 4: đại lý

**Tiêu đề:** `Dealers: one price level, learned during the week, and a menu at one margin`

**The idea:**
- `P(yes) is a logistic curve around a price level. The level is a sum: the week, the day, the dealer, the two towns, and 1% for each order we delivered to that dealer on time. Each answer moves every part it touched.`
- `We quote every option at the same margin: a slower option is worth €15, then €8 less to the dealer.`

**Why / bằng chứng** (17.999 báo giá ngẫu nhiên, dự báo đưa ra trước khi có câu trả lời):

| Our price against the learned level | Forecast yes | Actual yes |
|---|---|---|
| 10 to 15% above | 17.3% | 16.3% |
| 0 to 5% above | 42.0% | 39.9% |
| 0 to 5% below | 57.7% | 59.1% |
| 10 to 15% below | 82.7% | 81.7% |

**The effect:** `Euro gaps between options and lanes: €13,572 → €14,740 a week. One option instead of the menu: [€__].`

**Nói thật một điều (ghi nhỏ):** `A separate rule for the competitor's outage day earned nothing we could measure: −€59 a week (± 94) without it, on 115 weeks. The learner follows that day by itself.`

**Lời nói (25 giây):**
"On the dealer side, the desk learns one number during the week: the price level at which this dealer says yes half the time. Every answer updates it. The forecast is calibrated: when it says forty-two percent, we win forty percent. And we let the dealer choose the speed: every option is quoted at the same margin."

---

### Slide 7 · Ý 5: hai xe, một tài xế

**Tiêu đề:** `Two cars, one driver: a new car joins a waiting car when it starts where the other ends`

**The idea:** `Two cars share one gig when the second starts within 30 km of where the first ends, the drive is under five hours, and both cars are ready in time. The gig pays 0.75 × the two typical fees.`

**Why:** `A driver who delivers far from home has to travel back anyway. A car that goes the same way pays for that trip.`

**The effect:**
- `14 to 21% of cars travel in a two-car gig`
- `0.80 to 0.83 × the typical fee per car, against 0.94 to 0.99 × for a car alone`
- `Without pairs, same weeks: [€__ a week, __% on time]`

**Hộp nhỏ, "the bug that the numbers showed us":** `17 gigs paired a car that was not ready yet with a car due earlier. 18 cars arrived 14 to 89 hours late. One check now refuses such pairs: +€811 a week.`

**Lời nói (20 giây):**
"When a new car starts where a waiting car ends, one driver takes both, for three quarters of the two fees. The data also showed us a bug: we paired cars that were not ready yet. Eighteen cars arrived days late. One line fixed it, and that line was worth eight hundred euros a week."

---

### Slide 8 · Robust: vì sao tin được các con số

**Tiêu đề:** `The same weeks, one change at a time: €17,702 on 117 weeks it had never seen`

**Trên slide (4 ô):**

1. **Paired weeks.** `A seed gives the same week to the euro. On the same seeds, every difference is the change itself.`
2. **Unseen weeks.** `Tuned on 8 weeks: €17,704 a week. Played once on 117 new weeks: €17,702. All 117 ranked.`
3. **A night of tests, and one change taken.** `24 changes, one at a time, on 115 weeks. One was taken: gigs left from an earlier day are posted again each working morning, +€181 a week (± 84), and the worst week rose from 90.0% to 91.6% on time.`
4. **A restart and a live clock.** `Test final with a stop on purpose: €18,599, 95.8% on time, 0 of 1,030 requests missed. The desk rebuilds its books from the world's history and its own journal.`

**Hình gợi ý:** biểu đồ thanh 7 bậc (12,172 → 13,572 → 14,740 → 15,551 → 16,415 → 17,578 → 17,704), thanh bắt đầu từ 0.

**Lời nói (30 giây):**
"How do we know? The world repeats: the same seed gives the same week to the euro. So every comparison is on the same weeks with one change. We tuned on eight weeks, then played one hundred and seventeen new ones once. Seventeen thousand seven hundred and four euros became seventeen thousand seven hundred and two. All of them were ranked. And we stopped the desk on purpose during a test final: it came back and missed no request."

---

### Slide 9 · Giới hạn

**Tiêu đề:** `What did not work, what would break it, and what we do not know`

**Cột 1 · Did not work (€ a week, same weeks):**
- `A margin floor that follows the queue: −380 to −820`
- `Cheaper early orders to build a dealer's trust: −381`
- `On-time target 95% instead of 96%: +157, but 3 weeks under 91%`
- `Urgent fee 1.4 × instead of 1.6 ×: −505`
- `Nine more parts in the dealer model: no better forecast`

**Cột 2 · Would break it:**
- `One dealer's batch for a far town. 18 cars from Joensuu to Oulu found 1 driver in time. That week, 1 of 117, ended at exactly 90.0% on time. No general sign explained it, so a cap now refuses a car when 8 of ours already wait on the same long lane: that week ends at 91.4%.`
- `A week whose drivers are far from the 37 weeks we fitted: the fee model extrapolates.`
- `Minutes of downtime: the journal restores the desk, not the quotes it missed.`

**Cột 3 · We do not know:**
- `In weeks where every team earns most, we earned less than teams we beat overall (Sunday 03:00, week 4: €17,532 against €19,000 to €22,400). We found the cause on Sunday morning: after two days with 30 late cars, our own price of a late order rose from under €100 to €2,463, and the desk declined 41% of Wednesday's requests.` [THÊM 1 CÂU VỀ `ease` SAU KHI CÓ KẾT QUẢ THỬ]
- `Slope 12 earns more than the best-fitting 16. With the margin floor in the cost, we no longer know why.`

**Cuối slide · Sources and credits:** `Our practice runs tested driver capacity, fee timing, and pickup readiness for paired gigs. We also tested direct offers and left them out. The dealer-note reader is used under the MIT licence. Claude wrote most of the code and analysis. We chose what to test and what to keep.` [Nhật ký thí nghiệm](../research/NHAT_KY_THI_NGHIEM.md) · [Giấy phép bộ đọc ghi chú](../../engine/notes_exactum.py)

**Lời nói (25 giây):**
"Three honest limits. First, one week in a hundred and seventeen ended at exactly ninety percent: one dealer sent eighteen cars to one far town, and one found a driver in time. We looked for a general rule and found none, so we added a simple cap. Second, in the richest weeks, teams we beat overall earned more than we did. This morning we found why: after two bad days, our own price of lateness made the desk decline four requests in ten. Third, a flatter demand curve still earns more than the true one, and we cannot fully explain it."

**Ghi chú:** quy chế: "A team that shows its limits is easier to trust." Đừng cắt slide này khi thiếu thời gian. Cắt slide 6 hoặc 7 trước.

---

## 4. Hướng dẫn dựng slides

### 4.1 Luật trình bày (lấy từ mục "Say it clearly" của quy chế)

| Luật | Làm thế nào |
|---|---|
| Start with the answer | Slide 1 có kết quả và 3 ý. Không có slide "About us", "Agenda". |
| One idea on a slide | Tiêu đề là **một câu khẳng định có số**. Thân slide là bằng chứng cho đúng câu đó. |
| Unit + comparison cho mọi số | Viết `€17,578 a week, against €16,415 without it, on the same 8 weeks`. Không viết `17578`. |
| Show how it decides | Công thức, quy tắc, sơ đồ. **Không** ảnh chụp code. |
| Dùng từ của challenge | dealer, request, gig, fee, typical fee, deadline, list price, option. Xem bảng 4.2. |
| Cut what does not help | Không slogan, không danh sách dài, không logo trang trí. |
| Say what did not work | Slide 9. |

### 4.2 Bảng từ vựng: đừng tự đặt tên mới

| Đừng viết | Hãy viết |
|---|---|
| reserve, shadow price, congestion price | `a margin floor of 10% above the car's cost` (có thể gọi tắt *the price of a driver* sau khi đã định nghĩa) |
| late_fee, calm_eur, lane_cap (tên tham số) | mô tả bằng lời: `the fee of a car past its last pickup` |
| customer, client | `dealer` |
| job, task, trip | `gig` |
| reference fee, base fee | `typical fee` |
| tuning set / test set | `the 8 weeks we tuned on` / `117 weeks the desk had never played` |
| SLA, service level | `on-time share`, `the 90% delivery minimum` |

### 4.3 Bố cục

- 16:9. Lề rộng. Một màu nhấn duy nhất (dùng cho hàng "ours" trong bảng và cho con số hiệu quả).
- Cỡ chữ: tiêu đề ≥ 36 pt, thân ≥ 20 pt, chú thích nguồn ≥ 14 pt.
- Mỗi slide ý tưởng có đúng 3 khối theo thứ tự cố định: **What we saw** (trái trên) → **What the desk does** (trái dưới) → **bảng/hình + hiệu quả** (phải). Giữ nguyên vị trí qua các slide.
- Mỗi slide tối đa 1 bảng hoặc 1 hình. Bảng tối đa 6 hàng.
- Dòng nguồn ở chân slide: `Level 8, seeds halal-09 to halal-16, the same 8 weeks. ± is one standard error of the paired difference.`
- Biểu đồ thanh luôn bắt đầu từ 0.

### 4.4 Thứ tự cắt khi thiếu thời gian

1. Gộp slide 7 (pairs) vào slide 6 thành một slide "Dealers and pairs".
2. Bỏ bảng calibration ở slide 6, giữ một câu.
3. **Không cắt:** slide 1, 2, 3, 8, 9.

### 4.5 Kiểm trước khi nộp

- [ ] Mỗi con số có đơn vị và có so sánh.
- [ ] Mỗi con số tìm lại được trong `sweeps.jsonl`, `board.py` hoặc tài liệu nhật ký.
- [ ] Không còn ô `[__]`.
- [ ] Người thuyết trình đọc to từng dòng và giải thích được. Dòng nào không giải thích được thì xoá.
- [ ] 5 đến 10 slide.
- [ ] Xuất PDF. Mở PDF trên máy khác xem có vỡ font không.
- [ ] Submission hash (trang team), link code (repo public, mở được ở cửa sổ ẩn danh), slides.

---

## 5. Bài nói

### 5.1 Bản 60 giây (nếu chỉ được nói ngắn)

"Our desk runs on one idea: a car costs more than the fee we pay its driver. It costs the fee, the risk of arriving late, and the driver it takes from our other cars.

We found this through a paradox. A wrong demand curve earned more than the right one. The reason was that drivers, not dealers, are the scarce side. So every order must earn ten percent above its cost. That alone is worth eight hundred euros a week.

The second idea: a car that can no longer be on time stops paying the urgent fee. The third: each gig gets the one fee where fee plus risk is smallest, from a model of our own weeks.

We tuned on eight weeks and then played one hundred and seventeen new ones once: seventeen thousand seven hundred euros a week, all ranked. In the final we earned [__]."

### 5.2 Bản 4 phút

Đọc lần lượt phần "Lời nói" của slide 1 → 9 ở mục 3. Tổng khoảng 235 giây.

### 5.3 Ai nói gì (gợi ý cho 4 người)

| Người | Slide | Phải nắm chắc |
|---|---|---|
| A (mở và kết) | 1, 2, 9 | Ba công thức ở mục 2; ba giới hạn |
| B (tài xế) | 3, 4, 5 | Ba bảng số; vì sao 10%; vì sao 1,6 × rồi về 1,0 × |
| C (đại lý, ghép xe) | 6, 7 | Mức giá học thế nào; điều kiện ghép; lỗi ghép xe |
| D (bằng chứng) | 8 + trả lời câu hỏi về code | So cặp; 117 tuần; khởi động lại; cấu trúc repo |

Nếu chỉ một người nói: người đó đọc mục 2 và mục 6 ba lần.

---

## 6. Câu hỏi giám khảo dễ hỏi

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

## 7. Số còn thiếu và lấy ở đâu

| Ô trống | Lấy từ |
|---|---|
| Kết quả final | dòng `End` của `final.log`, và bảng xếp hạng final |
| Menu tắt, pairs tắt | `python sweep.py --summary tag=deck` (nếu kịp chạy) |
| Số đội có hạng ở vòng Chủ nhật 03:00 | `python board.py` |
