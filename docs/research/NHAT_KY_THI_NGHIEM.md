# Spread: nhật ký thí nghiệm

Mỗi dòng là một lượt chạy trên máy chủ, hoặc một phép phân tích trên các tuần đã lưu. Với mỗi lượt: **đổi gì → thấy gì → quyết định gì → thuộc ý nào.**

Giờ là giờ Việt Nam. Số tiền là € lợi nhuận mỗi tuần, cấp 8, trung bình trên các tuần ghi ở cột "Tuần thử". "±" là một sai số chuẩn của hiệu số có cặp (cùng tuần, chỉ đổi một thứ).

## Các ý (strategy) và mã

| Mã | Ý | Một câu |
|---|---|---|
| S0 | Nền | Bộ starter của kit + quy tắc cố định |
| S1 | Đại lý | Học mức giá dealer chấp nhận ngay trong tuần; menu nhiều tốc độ |
| S2 | Phí tài xế | Một mức phí cho mỗi gig, chọn từ mô hình khớp trên tuần của chính mình |
| S3 | 90% là một cái giá | Tỷ lệ đúng hạn tối thiểu được tính thành tiền trong chi phí từng xe |
| S4 | Ghép xe | Hai xe một tài xế khi xe sau bắt đầu ở nơi xe trước kết thúc |
| S5 | Giá của tài xế | Mỗi đơn phải lãi thêm 10% trên chi phí |
| S6 | Trễ là trễ | Xe quá giờ lấy cuối cùng thôi trả phí khẩn |
| S7 | Bảo hiểm | Chốt lô xe, đăng lại gig buổi sáng, khởi động lại |
| M | Đo thế giới | Tuần chơi ngẫu nhiên để lấy dữ liệu, khớp mô hình |

## Kết quả hiện tại (11:15 Chủ nhật)

| Thước đo | Số |
|---|---|
| 8 tuần dùng để chỉnh (halal-09 đến 16) | €17.704 |
| 117 tuần chưa từng chơi (bản đêm thứ Bảy) | €17.702 ± 386, 95,7% đúng hạn, 117/117 có hạng |
| Vòng xếp hạng tốt nhất | €96.850, hạng 2/55 (thứ Bảy 21:00 Helsinki) |
| Vòng gần nhất | €79.317 (Chủ nhật 03:00); hệ thống tốt nhất của ban tổ chức €56.128; bản khởi đầu −€362.463 |

---

## Giai đoạn 1 · Quy tắc cố định và bộ học giá đầu tiên (v1–v3)

Tuần thử: `test-1`, `test-2` (2 tuần). Mục đích: có một bot chạy được và hiểu các nút vặn.

| Bản / cấu hình | Kết quả | Đơn | Đúng hạn | Thấy gì | Quyết định | Ý |
|---|---|---|---|---|---|---|
| v1: `fee=1.0`, giá cố định | 6.446 | 244 | 97,6% | Rất an toàn nhưng nhận ít đơn | Mốc đầu | S0 |
| v2: `learn=true, fee=1.0` | 7.679 | 285 | 97,9% | Học giá trong tuần: +1.233, không mất đúng hạn | Giữ | S1 |
| v2: `fee=0.95, min_slack_h=5` | 7.814 | 326 | 95,1% | Phí thấp hơn một chút vẫn ổn | Giữ | S2 |
| v2: `fee=0.9, reserve=0.05` | 6.773 | 354 | 94,0% | Phí 0,9 × làm xe chờ lâu, trễ tăng | Bỏ | S2 |
| v2: `min_slack_h=3` (nhận xe gấp hơn) | 6.542 | 378 | 92,5% | Thêm đơn nhưng là đơn rủi ro | Bỏ | S3 |
| v2: thêm `max_km=700` | 4.200 | 363 | 87,9% | **0/2 tuần có hạng.** Tuyến rất dài phá tỷ lệ đúng hạn | Bỏ | S3 |
| v2: `late_eur=40, max_backlog=70` | 5.813 | 439 | 89,1% | 1/2 tuần mất hạng: phạt trễ quá nhẹ | Bỏ | S3 |

**Bài học giai đoạn 1:** nhận nhiều đơn hơn chưa chắc lãi hơn; ranh giới 90% rất gần. Các hằng số dò bằng tay không đi xa được.

---

## Giai đoạn 2 · Đo thế giới rồi khớp mô hình (M)

| Lượt | Làm gì | Kết quả | Dùng để |
|---|---|---|---|
| 16 tuần `explore` (`ex-1` đến `ex-16`) | Giá báo ngẫu nhiên 1,0–1,9 × list, phí ngẫu nhiên | −4.381/tuần, 77,8% đúng hạn (cố ý, không tính hạng) | Đường cầu của dealer: xác suất gật đầu theo giá |
| 16 tuần `try_fees` (`tf-1` đến `tf-16`) | Bot chơi bình thường, riêng phí mở đầu bốc ngẫu nhiên trong 6 mức | 8.119/tuần, 95,1% đúng hạn | Mô hình đúng hạn và phí thực trả |
| `fit.py` → `model.json` | Hồi quy logistic "đến đúng hạn" trên 7.235 xe; hồi quy tuyến tính "phí thực trả"; đường cầu trên 16.232 báo giá | Xe có tài xế trước cảnh báo: 2,4% trễ. Không có: 58,8% trễ. Một đơn trễ hoàn trung bình 0,47 × list | S1, S2 |
| Kiểm tra chéo (bỏ từng tuần ra) | Thử thêm dấu hiệu cho mô hình đúng hạn | Bộ 26 dấu hiệu hiện tại; thêm nữa không giảm log-loss | S2 |

**Thấy gì:** phí typical là một ngưỡng. Mở ở 0,70 × thì 87,4% đúng hạn; ở 1,00 × thì 97,4%; trên 1,00 × gần như không thêm gì.

---

## Giai đoạn 3 · Bản v4: mỗi quyết định là một bài tối ưu

| Bản / thay đổi | Tuần thử | Kết quả | Thấy gì | Quyết định | Ý |
|---|---|---|---|---|---|
| v4 gốc | test-1 | 8.451 (93,7%) | Mô hình thay hằng số | Giữ | S2 |
| v4 `on_time=0.90` | test-1 | 5.553 (89,5%) | **Mất hạng.** Nhắm đúng 90% là rơi | Bỏ | S3 |
| v4 `on_time=0.92` / `0.94` | test-1 | 6.685 / 6.459 | Mục tiêu thấp không lãi hơn | Chọn 0,96 | S3 |
| v4.2 gốc | test-1,2 | 9.110 (97,1%) | | | |
| v4.2 `pairs=true` | test-1,2 | 9.809 (96,5%) | Ghép xe: +699 | Giữ | S4 |
| v4.4 `pairs=true` | halal-09, 12 | 16.200 (91,8%) | Chỉ 2 tuần, không so được với mốc 8 tuần. Dùng để nghiên cứu gig hai xe nào có tài xế (`pairs_study.py`) | Nghiên cứu | S4 |
| Phí theo bậc cố định → phí từ mô hình | 8 tuần dùng để chỉnh | 12.172 → 13.572 | +1.400 | Giữ | S2 |
| Chênh lệch euro giữa các lựa chọn, theo tuyến | 8 tuần dùng để chỉnh | 13.572 → 14.740 | +1.168. Lựa chọn chậm hơn đáng giá ít hơn một số euro cố định (€15, rồi €8), không phải một tỷ lệ | Giữ | S1 |
| Kiểm tra "xe đã sẵn sàng" khi ghép | 8 tuần dùng để chỉnh | 14.740 → 15.551 | +811. 17 gig ghép xe chưa sẵn sàng với xe hạn sớm hơn; 18 xe trễ 14–89 giờ | Giữ | S4 |

---

## Giai đoạn 4 · Tối thứ Bảy: chi phí ẩn (v4.9e → v4.9g)

Tuần thử: 8 tuần halal-09 đến 16. Mốc: v4.9e = 15.551.

| Giờ | Lượt | Đổi gì | Kết quả | Thấy gì | Quyết định | Ý |
|---|---|---|---|---|---|---|
| 23:16 | 7 | `late_fee`, `slope=10`, `pair_hold=60` | `late_fee`: lỗi "No parameter"; slope 10: 15.633; pair_hold: 14.085 | Bản trên máy chủ là bản cũ: file đẩy lên bị kẹt. Từ đó luôn kiểm md5 | Sửa quy trình | — |
| 23:55 | 9 | `late_fee=1.0` | **16.415 (+864, 8/8 tuần)**, đúng hạn 94,6 → 95,2% | 15,1 xe/tuần nhận tài xế sau giờ lấy cuối: 100% trễ, đều trả 1,6 × | **Giữ** | S6 |
| 23:55 | 9 | `late_fee=0.85` / `1.15` | −257 / −246 so với 1,0 | 1,0 × là đúng chỗ | Bỏ | S6 |
| 23:55 | 9 | `invest=1.0` (bán rẻ để xây lòng tin) | −381 | 1% mỗi đơn đúng hạn không bù được phần giảm giá | Bỏ | S1 |
| 00:06 | 10 | `reserve=0.1` | **17.578 (+1.163, 8/8)**, đơn 527 → 483, đúng hạn 95,2 → 96,0% | Ít đơn hơn mà lãi hơn và đúng hạn hơn: bên khan hiếm là tài xế | **Giữ** | S5 |
| 00:06 | 10 | `reserve=0.2` / `0.3` | 17.317 / 15.837 | Đỉnh quanh 0,10–0,13 | Chọn 0,1 | S5 |
| 00:06 | 10 | `slope=8` / `6` (khi reserve = 0) | 16.813 / 16.108 | Đường cầu phẳng hơn chỉ lấy được một phần ba lợi ích của reserve | Bỏ | S5 |
| 00:17 | 11 | `reserve_q` (theo hàng đợi) | −380 đến −820 | Hàng đợi dài thì giá lên quá cao đúng lúc dealer đang mua | Bỏ | S5 |
| 00:17 | 11 | `on_time=0.95` | −266 | | Bỏ | S3 |
| 00:17 | 11 | `urgent_fee=1.4` | −505 | Phí khẩn thấp thì xe gấp không có tài xế | Bỏ | S2 |
| 00:36 | 12 | `calm_eur=150` | **17.704 (+126)** | Phí cao hơn chủ yếu kéo tài xế từ xe này sang xe khác của ta | **Giữ** | S2 |

---

## Giai đoạn 5 · Đêm thứ Bảy: kiểm trên tuần chưa từng chơi (v4.9h)

| Giờ | Lượt | Làm gì | Kết quả | Thấy gì | Quyết định | Ý |
|---|---|---|---|---|---|---|
| 01:00 | Test final | Đồng hồ thật, cố ý tắt bot ở phút 14 rồi để tự chạy lại | €18.599, 500 đơn, 95,8% đúng hạn; 1.030 request, **0 bị lỡ** | Bot dựng lại đơn, gig và niềm tin về dealer từ lịch sử + nhật ký | Cơ chế khởi động lại đạt | S7 |
| 01:34–09:30 | Đêm | Bản gốc + 24 thay đổi, mỗi lần một thứ, trên tuần `night-N` mới | Gốc: **17.702 ± 386 trên 117 tuần**, 95,7% đúng hạn | Ba ý chính giữ nguyên ngoài mẫu (3 dòng dưới) | | |
| | | `reserve=0` | −809 ± 121 | Giá của tài xế đứng vững | Xác nhận | S5 |
| | | `late_fee=0` | −453 ± 68 | Trễ là trễ đứng vững | Xác nhận | S6 |
| | | `calm_eur=300` | −149 ± 70 | Phí êm hơn đứng vững | Xác nhận | S2 |
| | | `outage=0` | −59 ± 94 | Luật riêng cho ngày đối thủ sập **không đo được lợi ích**: bộ học giá tự bám theo ngày đó | Ghi vào giới hạn | S1 |
| | | `morning=true` | +133 ± 107 (69 tuần) → **+181 ± 84 (115 tuần)**; tuần tệ nhất 91,6% thay vì 90,0% | Đăng lại gig tồn mỗi sáng: tài xế trong ngày được báo có gig mới | **Bật** (sáng CN) | S7 |
| | | `on_time=0.95` | +157 ± 113, nhưng 3 tuần dưới 91% | Lợi nhỏ, rủi ro mất hạng lớn | Bỏ | S3 |
| | | `reserve=0.15`, `reserve_tight` 1 / 2 | +14; −346 / −222 | Không có tín hiệu nào báo sớm tuần chật | Bỏ | S5 |
| | | `pair_hold=60` | +114 nhưng 1 tuần mất hạng | | Bỏ | S4 |
| | | `look_h=3`, `pair_max_h=7`, `urgent_fee=1.8`, bỏ mức phí 0,7 | −649, −303, −125, −258 | | Bỏ | S2, S4 |

**Bài học giai đoạn 5:** 8 tuần chỉnh cho 17.704; 117 tuần mới cho 17.702. Không có dấu hiệu khớp quá mức.

---

## Giai đoạn 6 · Sáng Chủ nhật: tuần xấu nhất và tuần giàu nhất

| Giờ | Lượt | Làm gì | Kết quả | Thấy gì | Quyết định | Ý |
|---|---|---|---|---|---|---|
| 06:30–07:00 | Phân tích | Mổ tuần `night-30` (90,0%) | 1 dealer gửi 18 xe Joensuu → Oulu trong một buổi sáng; 1 xe có tài xế kịp giờ | Sự cố của một lô xe, không phải lỗi chung | | S7 |
| 07:00 | Phân tích | 9 dấu hiệu "tải" trên 16 + 5 tuần | Log-loss không đổi (0,1466), \|z\| < 1,5 | Không có quy luật chung | Không thêm vào mô hình | S2 |
| 10:24 | Vòng xếp hạng CN 03:00 | Bản `c4a795fb`, mặc định | 16.830 / 15.967 / 10.992 / 17.532 / 17.995 = **€79.317** | Tuần 4: cả bảng €19–21k, ta 17,5k | Mổ tuần 4 (dòng dưới) | |
| 10:52 | Sweep | `backup=1.26` (đường cầu ngày đối thủ sập = đường thường dịch lên 26%) | +74 ± 114 (60 tuần) | Khớp dữ liệu tốt hơn nhưng không ra tiền | Bỏ | S1 |
| 10:52 | Sweep | `lane_cap=8` (không nhận thêm khi 8 xe của ta đang chờ trên cùng tuyến ≥ 200 km) | Chỉ 3/60 tuần đổi: `night-30` **+1.464, 90,0 → 91,4%**; hai tuần khác −173, −120 | Bảo hiểm gần như miễn phí | **Bật** | S7 |
| 11:00 | Phân tích | Mổ tuần 4 theo ngày | T2–T3 thắng 62% và 58% request, 30 xe trễ. T4: "giá của một đơn trễ" lên €2.463–4.800, bot từ chối 41% request | Bot tự bóp phanh 2 ngày dù cả tuần kết thúc ở 93,4% | Thử `ease` | S3 |
| 11:00 | Sweep | Bản chốt `tag=final` (= `morning` + `lane_cap`) trên 60 tuần | *đang chạy* | | | S7 |
| 11:20 | Sweep | `ease=0.01` (+ trần `ease_top=0.06`): sau ngày xấu, chỉ tính phí rủi ro cho xe rủi ro hơn mức trễ hiện tại của tuần | *đang chạy* | Chạy lại tuần 4 trên máy: giá báo T4–T6 về ×1,27–1,36 thay vì ×1,42–1,60 | *chờ số* | S3 |

---

## Vòng xếp hạng (5 tuần bí mật, mọi đội chơi cùng tuần)

| Vòng (giờ Helsinki) | Bản | Từng tuần | Tổng | Hạng | Ghi chú |
|---|---|---|---|---|---|
| Thứ Bảy 18:00 | v4.9e hoặc f | | €82.454 | 3 / 67 | Hạng 1: €94.445 |
| Thứ Bảy 21:00 | v4.9h | 19.345 / 20.581 / 18.801 / 20.537 / 17.586 | €96.850 | 2 / 55 | Hạng 1: €105.424. Yếu ở tuần 2 và 4 |
| Chủ nhật 03:00 | v4.9k mặc định | 16.830 / 15.967 / 10.992 / 17.532 / 17.995 | €79.317 | khoảng 5 / 48 | Hạng 1: €88.416. Hệ thống tốt nhất của ban tổ chức: €56.128 |
| Chủ nhật 06:00 | bản chốt | *chưa chơi* | | | Tổng duyệt cho final |

---

## Phân tích không cần máy chủ (trên các tuần đã lưu)

| Câu hỏi | Dữ liệu | Thấy gì | Dẫn tới |
|---|---|---|---|
| Đường cầu có đúng không? | 17.999 báo giá ngẫu nhiên, 21 tuần | Dự báo 42,0% → thực tế 39,9%; 82,7% → 81,7%. Độ dốc 16 khớp tốt nhất (log-loss 0,2964 so với 0,3025 ở 12) | Lợi ích của đường phẳng không đến từ dealer → ý S5 |
| Bộ học giá còn thiếu phần nào? | Thêm 9 phần (dealer × ngày, loại xe, giờ, …) | Không phần nào giảm log-loss | Dừng mở rộng S1 |
| Đối thủ có phản ứng không? | Các tuần explore | Mức giá của một dealer thấp hơn khoảng 1,6% vào hôm sau khi ta thắng ≥ 30% request của họ | Quá nhỏ, không dùng |
| Xe nào nhận tài xế muộn? | 24 tuần | 15,1 xe/tuần sau giờ lấy cuối, 100% trễ, đều trả 1,6 × | Ý S6 |
| Có nên chào gig trực tiếp cho tài xế? | Thử nghiệm riêng của đội | Dữ liệu của lượt thử chưa được lưu trong repo này | Không đưa vào bản final |
| Bản mới có đổi hành vi ngoài ý muốn không? | Chạy lại tuần đã lưu qua hai bản, so từng hành động | 2.503 / 2.510 / 2.370 hành động trùng 100% khi công tắc tắt | Mỗi bản mới đều qua bước này |

---

## Quy tắc quyết định (không đổi suốt cuộc thi)

1. Một thay đổi mỗi lần, thêm dưới dạng công tắc mặc định tắt.
2. So trên cùng tuần (cùng seed cho cùng một tuần tới từng euro).
3. Bật khi lợi ≥ max(€250, 1,5 × sai số chuẩn) và không thêm tuần nào dưới 91%.
4. Chỉnh trên 8 tuần, xác nhận trên tuần chưa từng chơi.

**Một ngoại lệ, ghi rõ:** `morning=true` được bật ở +€181 (dưới ngưỡng €250). Lý do: nó được đánh dấu lúc có 69 tuần (+133), và 46 tuần chạy thêm sau đó cho khoảng +250, tức kết quả lặp lại trên dữ liệu mới; đồng thời nó nâng tuần tệ nhất từ 90,0% lên 91,6%.
