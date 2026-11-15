# MathNet1 · Spread: kế hoạch ngày final

Viết lúc 11:00 VN, Chủ nhật 15/11. Mọi giờ dưới đây là **giờ Việt Nam** (Helsinki + 5 tiếng).

## 1. Hai cửa phải qua

| Cửa | Khi nào | Ai chấm | Điều kiện |
|---|---|---|---|
| 1. Vào top 10 | 14:00–14:35, một tuần bí mật cấp 8 | Margin của đúng 1 tuần | ≥ 90% đơn đúng hạn, margin trong 10 đội cao nhất |
| 2. Top 3 của challenge | 15:30–19:00, giám khảo gặp 10 đội | Elegant, clear, creative, robust | Bài nộp trước 15:00 và phần trình bày |

Quy chế viết rõ: *"Reaching the top 10 is enough. After that, the jury judges how you built your system, and your margin no longer counts."*

Hệ quả cho kế hoạch:

- Về margin, mục tiêu nội bộ là **top 5**, để còn đệm nếu các đội khác mạnh lên. Hạng 4 hay hạng 9 thì giá trị như nhau trước giám khảo.
- Không có kế hoạch nào **bảo đảm** top 3. Kế hoạch này làm ba việc: không tự làm hỏng cửa 1, tăng xác suất qua cửa 1, và chuẩn bị cửa 2 xong trước khi final bắt đầu.

## 2. Ta đang đứng ở đâu so với các đội khác

### 2.1 Tổng 5 tuần: hạng 2 đến 4

| Vòng (giờ Helsinki) | MathNet1 | Hạng | Hạng 1 | Hạng 10 |
|---|---|---|---|---|
| Thứ Bảy 18:00 | €82.454 | 3 / 67 | €94.445 | €75.405 |
| Thứ Bảy 21:00 | €96.850 | 2 / 55 | €105.424 (Juhus) | €86.201 |
| Chủ nhật 03:00 | €79.317 | khoảng 5 / 48 | €88.416 (Progresful) | €76.873 |

### 2.2 Từng tuần: không ổn định

Final chỉ là **một tuần**. Hạng của ta theo từng tuần ở vòng Chủ nhật 03:00, so với 15 đội đầu bảng:

| Tuần | Ta | Đội đầu | Đội thứ 10 trong tuần | Hạng của ta |
|---|---|---|---|---|
| 1 | 16.830 | 18.156 | 15.256 | 5 |
| 2 | 15.967 | 16.197 | 14.246 | 2 |
| 3 | 10.992 | 12.520 | 11.045 | 10 |
| 4 | 17.532 | 20.920 | 19.636 | **15** |
| 5 | 17.995 | 19.346 | 17.077 | 4 |

- 5 đội mạnh chưa chơi vòng đó (Juhus, Progresful, Edge101, Team Moonshot, DaVinci's Night Shift). Cộng họ vào thì mỗi hạng trên lùi thêm 3 đến 5 bậc.
- Ước lượng thẳng thắn (với bản sáng nay): xác suất ta vào top 10 trong một tuần bất kỳ khoảng **55 đến 70%**. Vòng thứ Bảy 21:00 thì cả 5 tuần ta đều trong top 8.
- Mốc so sánh từ ban tổ chức, cùng 5 tuần đó: House best €56.128, House starter −€362.463.

### 2.3 Các đội đầu bảng kiếm tiền kiểu khác ta

| Đội | Đơn mỗi tuần | € mỗi đơn |
|---|---|---|
| Juhus | 473 | 43,3 |
| Progresful | 464 | 41,4 |
| Seekers | 402–416 | 42,5–45,5 |
| Edge101 | 417 | 43,9 |
| **MathNet1** | **458–526** | **34,6–36,8** |

Họ lấy ít đơn hơn và lãi nhiều hơn trên mỗi đơn. Ta lấy nhiều đơn, lãi mỏng hơn. Ở tuần "giàu" (tuần 4), cách của họ thắng rõ: ta nhận 275 đơn trong hai ngày đầu, đến thứ Tư tỷ lệ đúng hạn rơi xuống 87,2%.

Nguyên nhân đã tìm ra lúc 11:00 (xem mục 3): không phải ta bán quá rẻ, mà là sau hai ngày đầu nhiều xe trễ, bot tự ngừng bán gần hai ngày. Lời giải (`ease`) đang được thử; chưa có số thì chưa bật.

## 3. Phần margin: làm gì trong 2 tiếng còn lại

Nguyên tắc giữ nguyên như cả cuộc thi: chỉ bật một thứ khi nó thắng trên cùng các tuần, theo quy tắc đặt trước.

**Quy tắc bật:** lợi ≥ max(€250, 1,5 × sai số chuẩn) trên 69 tuần, và không thêm tuần nào dưới 91%. Riêng cái chốt bảo hiểm (`lane_cap`): bật nếu tuần night-30 tăng ≥ 1 điểm đúng hạn và tổng các tuần khác không âm.

| Việc | Trạng thái | Quyết định |
|---|---|---|
| `backup=1.26` (đường cầu ngày đối thủ sập) | Đã thử: €17.637 so với €17.642 | **Không bật** |
| `lane_cap=8` (chốt lô xe trên tuyến dài) | Chỉ 3/60 tuần đổi: tuần xấu +€1.464 và 90,0 → 91,4%; hai tuần khác −173, −120 | **Bật** |
| `morning=true` (đăng lại gig tồn mỗi sáng) | +€181 ± 84 trên 115 tuần; tuần tệ nhất 91,6% | **Bật** (dưới ngưỡng €250, nhưng lặp lại trên 46 tuần mới) |
| Mổ tuần 4 của vòng sáng nay | Xong: sau 2 ngày có 30 xe trễ, "giá của một đơn trễ" vọt lên €2.463–4.800 và bot từ chối 41% request hôm thứ Tư | Thử công tắc `ease` (dòng dưới) |
| `ease=0.01` + trần `ease_top=0.06` | Đang chạy trên 60 tuần | Bật nếu lợi ≥ €250 và ≥ 1,5 sai số, không tuần nào dưới 91% |
| Vòng xếp hạng cuối (mở 11:00) | Chơi bằng cấu hình đã chốt | Tổng duyệt, không đổi gì sau đó |

**Chốt cấu hình lúc 12:30.** Sau giờ đó không đổi gì nữa, kể cả khi có ý hay.

Cấu hình sẽ chạy final nếu `ease` không vượt quy tắc: bản chốt (`4ce23b14` hoặc `91dda7db`, hành vi giống hệt nhau) = bản đêm qua + `morning` + `lane_cap`. Bản cũ được giữ trên máy chủ dưới tên `dispatch_c4a795fb.py` để quay lui.

## 4. Lịch chi tiết

| Giờ | Việc | Ai |
|---|---|---|
| 11:00–11:20 | Dán `weeks.py`, `board.py house 3`, dòng tổng kết; scp file tuần xếp hạng | Triết |
| 11:00–12:15 | Dựng slides theo `PITCH_NOTES.md` | Thành viên làm slides |
| 11:20–12:00 | Đọc kết quả, mổ tuần 4, quyết định `lane_cap` | Claude |
| 12:00–12:15 | Chơi vòng xếp hạng cuối (5 tuần, trong tmux, không Ctrl-C) | Triết |
| 12:15–12:30 | Chạy số còn thiếu cho slides (starter, tắt pairs, tắt menu) | Triết |
| **12:30** | **Chốt cấu hình** | cả team |
| 12:30–13:10 | Tạo repo public, đẩy code + README; kiểm link ở cửa sổ ẩn danh | Triết + 1 người |
| 12:30–13:30 | Tập nói 2 lượt theo mục 5 của `PITCH_NOTES.md`; hỏi nhau 12 câu ở mục 6 | Người thuyết trình |
| **13:15** | **Chạy final** (mục 5) | Triết |
| 13:30 | Đóng đăng ký final. Kiểm bot đang in `Final world ...` hoặc đang chờ | Triết |
| 14:00–14:35 | Final chạy. **Không đụng vào máy chủ.** Chỉ nhìn | Triết |
| 14:35–14:50 | Điền kết quả vào slides và README; xuất PDF | cả team |
| **14:50** | **Nộp:** submission hash + link code + slides | Triết |
| 15:00 | Hạn nộp | |
| 15:30–19:00 | Gặp giám khảo nếu vào top 10 | cả team |

## 5. Chạy final: từng lệnh

Trên máy chủ, trong phiên tmux cũ:

```
tmux attach -t main
set -a; source .env; set +a
cd ~/spread-bot && source .venv/bin/activate
md5sum dispatch.py | cut -c1-8
python board.py | tail -3
bash final.sh
```

- `md5sum` phải ra đúng mã của bản đã chốt.
- `board.py` chạy được nghĩa là key đã nạp.
- Bot được phép chạy sớm: nó tự chờ đến khi final bắt đầu.
- Thoát khỏi tmux mà không dừng bot: `Ctrl-b` rồi `d`. Quay lại: `tmux attach -t main`.

### Nếu có sự cố trong lúc final

| Sự cố | Làm gì |
|---|---|
| Cửa sổ SSH đứt | SSH lại, `tmux attach -t main`. Bot vẫn chạy trong tmux |
| Bot dừng vì lỗi | `final.sh` tự chạy lại sau 3 giây và nối lại đúng tuần đó. Không làm gì |
| Vòng lặp báo `SPREAD_KEY is not set` | Ctrl-C hai lần, `set -a; source .env; set +a`, `bash final.sh` |
| Máy chủ chết hẳn | Chạy từ laptop: mở PowerShell trong `C:\Users\HP\spread-bot`, bật venv, nạp key, `python dispatch.py --final`. Bot dựng lại đơn và gig từ máy chủ ban tổ chức |
| Tỷ lệ đúng hạn tụt giữa tuần | **Không can thiệp.** Bot tự tăng giá của đơn rủi ro. Dừng bot chỉ làm mất đơn |

Quy chế: khi bot dừng, request chuyển sang đối thủ và tài xế vẫn chạy. Vì vậy mỗi giây dừng là mất tiền, nhưng không mất đơn đã nhận.

## 6. Bài nộp (trước 15:00)

- [ ] **Submission hash**: lấy ở trang team. Chép sẵn vào một file từ 13:30.
- [ ] **Link code**: repo public. Trong repo: `dispatch.py`, `world.py`, `fit.py`, `model.json`, `notes_exactum.py` (giữ nguyên header MIT), `sweep.py`, `weeks.py`, `night.py`, `final.sh`, `check_final.py`, `replay_test.py`, `restart_test.py`, `README.md`. **Không** đưa `.env`, `runs/`, `.venv/`.
- [ ] **Slides**: 5 đến 10 slide, PDF. Phương án dự phòng nếu không kịp dựng mới: bộ slides Claude dựng hôm thứ Bảy vẫn còn, chỉ thiếu 4 con số.
- [ ] Trong slides và README, dẫn [nhật ký thí nghiệm](../research/NHAT_KY_THI_NGHIEM.md) cho các quyết định về nguồn tài xế, mốc sáu giờ và chào trực tiếp. Dẫn [thông tin nguồn và giấy phép MIT của bộ đọc ghi chú](../../engine/notes_exactum.py). Ghi công Claude viết phần lớn code và phân tích.

## 7. Kịch bản

**A. Vào top 10 (kỳ vọng chính).** Nộp đúng hạn. Từ 15:30 trình bày theo `PITCH_NOTES.md`. Điểm mạnh của ta trước giám khảo: một ý xuyên suốt, mỗi ý có số đo trên cùng tuần, 69 tuần chưa từng chơi, và nói thật về giới hạn.

**B. Có hạng nhưng ngoài top 10.** Vẫn nộp đầy đủ trước 15:00: quy chế yêu cầu mọi đội nộp, và ban tổ chức chạy lại từng tuần để kiểm điểm, thứ hạng có thể đổi.

**C. Tuần final dưới 90% đúng hạn.** Không có hạng. Vẫn nộp. Xác suất ước tính 1 đến 2% (1 tuần trong 69 tuần thử rơi đúng 90,0%).

## 8. Sau khi xong

- Xoá các máy chủ Verda (kể cả máy V100 không dùng) để khỏi bị tính tiền.
- Giữ lại `sweeps.jsonl`, `final.log` và thư mục `runs/` trước khi xoá máy: đó là bằng chứng cho mọi con số trên slides.
