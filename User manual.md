# Hướng Dẫn Sử Dụng Idol Showdown Autobot (User Manual)

Tài liệu này cung cấp hướng dẫn chi tiết cách vận hành, cấu hình phím nhấn, soạn thảo combo và khắc phục lỗi khi sử dụng phần mềm **Idol Showdown Autobot**.

---

## 📌 1. Tổng Quan Về Giao Diện

Giao diện ứng dụng được chia thành 5 phân hệ chính truy cập qua thanh Sidebar bên trái:

### ⚙️ Cấu Hình Chung (General Settings)
*   **Tiến trình Game (Game Process)**: Tên file chạy của game (mặc định: `Idol Showdown.exe` hoặc `notepad.exe` để thử nghiệm).
*   **Cửa sổ Game (Game Window)**: Tên tiêu đề cửa sổ game (mặc định: `Idol Showdown` hoặc `Notepad` để thử nghiệm).
*   **Phím tắt Bắt đầu/Dừng (Start/Stop Hotkey)**: Phím tắt toàn cục để kích hoạt (`F9`) hoặc tắt bot (`F10`) ngoài màn hình.
*   **Khoảng nghỉ đòn (Delay Frames)**: Số khung hình dừng nghỉ giữa các đòn đánh liên kết bởi toán tử `,` (1 giây = 60 frames, mặc định: 30 frames).
*   **Hướng đứng của P2 (Facing Direction)**: Chọn bên sân đứng của Player 2 để bot tự động xoay hướng phím bấm:
    *   *Bên phải (Facing Left)*: Phím di chuyển Trái/Phải tự động bị đảo ngược.
    *   *Bên trái (Facing Right)*: Giữ nguyên hướng phím di chuyển chuẩn.

### ⌨️ Phím Điều Khiển Player 2 (P2 Key Bindings)
*   Nơi cấu hình **12 phím bấm ảo** tương ứng với cài đặt nút bấm của Player 2 trong game.
*   Nhấp vào từng ô nhập liệu, gõ phím mong muốn, sau đó nhấn **Lưu Cấu Hình Phím** ở góc dưới cùng để đồng bộ phím bấm.

### 📝 Trình Tạo Combo (Combo Custom Panel)
*   **Tên Combo**: Tên gợi nhớ cho chuỗi đòn.
*   **Chuỗi Combo**: Nhập các nút bấm theo cú pháp (xem thêm ở phần 3).
*   **Chạy Thử Combo**: Nhấn nút này để hệ thống đợi 3 giây (đủ để bạn click chọn cửa sổ game) và thực thi kiểm thử chuỗi phím bấm vừa soạn thảo lên game.

### 📂 Danh Sách Combo & Playlist (Move List Manager)
*   Hiển thị danh sách tất cả các Combo hiện có sắp xếp theo từng Playlist (ví dụ: `test_1`, `pressure_string`).
*   **Kích hoạt nhanh**: Nhấp nút **Play** ở bên phải đòn đánh để bot thi triển nhanh đòn đánh đó lên game (đợi 1 giây để bạn click cửa sổ game).
*   **Chỉnh sửa/Xóa**: Thay đổi nội dung combo hoặc xóa khỏi bộ nhớ.

### 🩺 Chẩn Đoán Hệ Thống (Diagnostics & Logs)
*   Hiển thị thông tin hệ thống và toàn bộ lịch sử hoạt động, thời điểm gửi phím ảo, và các thông báo lỗi nếu có.

---

## ⌨️ 2. Điều Khiển Bằng Phím Tắt Toàn Cục

Bạn có thể điều khiển bot trực tiếp khi đang ở trong cửa sổ game mà không cần bật giao diện:
*   **Nhấn phím `F9` (hoặc phím Start cấu hình)**: Bắt đầu chạy vòng lặp playlist tự động được chọn (nút trên giao diện chuyển sang `ACTIVE`).
*   **Nhấn phím `F10` (hoặc phím Stop cấu hình)**: Tắt ngay lập tức vòng lặp bot và giải phóng toàn bộ phím ảo đang nhấn (nút giao diện chuyển sang `STOPPED`).

---

## 🔣 3. Hướng Dẫn Soạn Thảo Cú Pháp Combo

Hệ thống hỗ trợ cú pháp **Numpad Notation** tiêu chuẩn của dòng game đối kháng kết hợp với các toán tử liên kết thời gian thông minh:

### Hướng di chuyển (Numpad):
Nhìn vào bàn phím số (Numpad) trên bàn phím máy tính để xác định hướng (mặc định cho nhân vật đứng bên trái nhìn sang phải):
*   `7` (Nhảy lùi) | `8` (Nhảy lên) | `9` (Nhảy tiến)
*   `4` (Đi lùi)   | `5` (Đứng im)   | `6` (Đi tiến)
*   `1` (Đỡ thấp)  | `2` (Ngồi)      | `3` (Ngồi tiến)

### Phím Tấn Công (Actions):
*   `L` : Đòn nhẹ (Light Attack)
*   `M` : Đòn trung (Medium Attack)
*   `H` : Đòn mạnh (Heavy Attack)
*   `S` : Đòn đặc biệt (Special Attack)
*   `B` : Burst
*   `CL` : Gọi đồng đội (Collab)

### Toán tử liên kết (Operators):
*   **`"+"` (Cùng lúc)**: Nhấn các phím đồng thời.
    *   *Ví dụ*: `2+H` (Ngồi Heavy), `L+M` (Ném/Grab).
*   **`">"` (Cancel nhanh)**: Nhấn nút tiếp theo ngay lập tức sau **5 frames** (khoảng 0.08 giây). Dùng cho các chuỗi Gatling combo liên hoàn.
    *   *Ví dụ*: `5L > 5M > 5H` (Đấm nhẹ -> Đấm trung -> Đấm mạnh liên tục).
*   **`","` (Chờ nhịp/Link)**: Nghỉ một khoảng bằng `delay_frames` (mặc định 30 frames ~ 0.5 giây) rồi mới thực hiện hành động tiếp theo. Dùng để kết nối giữa các chiêu thức riêng biệt hoặc chờ đối thủ rơi xuống.
    *   *Ví dụ*: `236H, 623L` (Thi triển chiêu 236H, chờ hồi chiêu/hết động tác rồi thi triển tiếp 623L).

---

## 🎮 4. Quy Trình Sử Dụng Chuẩn (Step-by-Step)

1.  **Mở Game**: Khởi chạy tựa game *Idol Showdown*.
2.  **Cấu hình phím trong game**: Xem phím bấm Player 2 trong game đang gán là gì.
3.  **Khởi động Autobot**: Nhấp đúp chạy file `Idolshowdown_autobot.exe`.
4.  **Đồng bộ phím**: Nhập chính xác 12 phím của Player 2 vào tab **P2 Key Bindings** của Autobot rồi nhấn lưu.
5.  **Chọn Playlist**: Tại tab **General Settings**, chọn playlist combo bạn muốn dùng và chọn hướng đứng của nhân vật Player 2.
6.  **Vào trận đấu**:
    *   Click vào cửa sổ game Idol Showdown.
    *   Nhấn phím `F9` để bot bắt đầu chạy playlist đòn đánh tự động.
    *   Nhấn phím `F10` bất kỳ lúc nào để dừng lại.

---

## 🛠️ 5. Khắc Phục Lỗi Thường Gặp

### Lỗi 1: Bot đã báo gửi phím thành công nhưng nhân vật trong game không di chuyển
*   **Nguyên nhân**: Game không được active (mất focus) hoặc game chặn các lệnh mô phỏng phím bấm của DirectInput.
*   **Khắc phục**:
    1.  Chắc chắn rằng bạn đã nhấp chuột chọn cửa sổ game trước khi bot gửi phím.
    2.  Đảm bảo game đang chạy ở chế độ **Windowed (Cửa sổ)** hoặc **Borderless Windowed (Không viền)**. Tránh chạy Fullscreen (Toàn màn hình) vì Windows API có thể chặn mô phỏng phím bấm.
    3.  Hãy thử chạy file `Idolshowdown_autobot.exe` dưới quyền Administrator (Run as Administrator) nếu Windows UAC chặn tín hiệu bàn phím ảo.

### Lỗi 2: Nhấn phím tắt F9 / F10 không hoạt động
*   **Nguyên nhân**: Một phần mềm khác trên Windows (như Discord, Steam hoặc trình duyệt) đã đăng ký phím tắt F9/F10 trước đó, gây ra xung đột (lỗi Error Code 1409 trong phần Diagnostics).
*   **Khắc phục**: Truy cập tab **General Settings**, thay đổi phím tắt Start/Stop sang một phím khác (ví dụ: `F5`, `F6` hoặc `F7`), nhấn lưu cấu hình và khởi chạy lại.

### Lỗi 3: Combo thực hiện bị đứt quãng, không ra đủ chiêu
*   **Nguyên nhân**: Tốc độ khung hình (FPS) của game bị tụt hoặc nhịp độ delay giữa các chiêu thức không đúng.
*   **Khắc phục**:
    1.  Nếu đòn đánh ra quá chậm, hãy giảm chỉ số **Delay Frames** trong tab Cài đặt xuống (ví dụ từ 30 xuống 20 hoặc 15).
    2.  Sử dụng ký tự `>` thay vì dấu `,` đối với các đòn đánh yêu cầu nối nút nhanh (như chuỗi đánh thường).
