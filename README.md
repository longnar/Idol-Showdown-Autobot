# Idol Showdown Autobot - Phiên bản V0.102

Chào mừng bạn đến với **Idol Showdown Autobot (V0.102)**, một công cụ mạnh mẽ giúp tự động hóa chuỗi combo và di chuyển đòn đánh cho người chơi số 2 (Player 2) trong tựa game đối kháng Idol Showdown. 

Ứng dụng được xây dựng trên mô hình kết hợp giữa **Backend Python (Flask)** để quản lý logic phím tắt, ghi phím, và lập lịch thi triển combo, kết hợp với **Frontend Rust Ratatui (TUI)** làm giao diện dòng lệnh trực quan, nhẹ nhàng và phản hồi cực nhanh.

---

## 🌟 Các Tính Năng Nổi Bật

*   🖥️ **Giao diện Terminal (TUI) hiện đại**: Được viết bằng Rust (Ratatui), cung cấp giao diện quản lý trực quan và nhẹ nhàng ngay trong cửa sổ dòng lệnh.
*   ⌨️ **Lắng nghe phím tắt toàn cục (Global Hotkeys)**: Tự động đăng ký phím tắt toàn hệ thống (mặc định `F3` để bắt đầu, `F4` để dừng) giúp bạn dễ dàng kích hoạt/tắt bot khi đang tập trung chơi game.
*   ⚡ **Bộ phân tích Combo tối ưu (Smart Parser)**:
    *   **Phím gộp (`"+"`)**: Thực hiện nhấn các phím ảo cùng một thời điểm (ví dụ: `2+H`, `L+M`).
    *   **Cancel nhanh (`">"`)**: Chuyển đổi đòn đánh ngay lập tức sau **5 frames** (~0.08 giây) giúp chuỗi Gatling/Combo không bị rụng giữa chừng.
    *   **Chờ nhịp (`","`)**: Tạo khoảng trễ giữa các khối đòn đánh bằng đúng số frames thiết lập trong cấu hình `delay_frames` trên giao diện.
*   🔄 **Hỗ trợ đảo hướng phím bấm (Player 2 Side)**: Tự động đổi hướng phím di chuyển (Trái/Phải, Tiến/Lùi) dựa theo vị trí của Player 2 trên sân đấu (Bên phải hướng sang trái hoặc Bên trái hướng sang phải).
*   📁 **Quản lý Playlist & Combo trực quan**: Tạo, chỉnh sửa, xóa combo và gán chúng vào các Playlist cấu hình khác nhau trực tiếp qua giao diện TUI.
*   🩺 **Bảng giám sát Logs thời gian thực**: Theo dõi từng phím nhấn ảo được thi triển lên trò chơi trực tiếp tại giao diện Diagnostics.

---

## 🚀 Hướng Dẫn Vận Hành

### ⚠️ LƯU Ý QUAN TRỌNG
Nếu khi chạy không thấy player 2 có hành động gì trong game:
1. **Kiểm tra tiến trình và tên cửa sổ**: Mở file `config.json` và kiểm tra cấu hình game.
   * Để chạy với game, đảm bảo có: `"game_process": "idol showdown.exe"`, `"game_window": "Idol Showdown"`.
   * Bạn có thể đổi sang `"notepad.exe"` / `"Notepad"` để kiểm tra bot gõ phím trực tiếp trên phần mềm Notepad.
2. **Kiểm tra Unikey / bộ gõ tiếng Việt**: Đảm bảo tắt chế độ gõ tiếng Việt (hoặc chuyển sang tiếng Anh) để tránh việc phím nhấn ảo bị dịch sai ký tự (ví dụ: `W` thành `Ư`).
3. **Chạy dưới quyền Administrator**: Nếu game chặn phím ảo, hãy chạy công cụ dưới quyền Administrator.

### Cách 1: Chạy trực tiếp từ File Thực thi (.exe)
1. Truy cập thư mục [dist/](file:///l:/Code%20Project/fighting_game_bot%20-%20ratatui/dist/).
2. Nhấp đúp chuột hoặc chạy tệp [Idolshowdown_autobot.exe](file:///l:/Code%20Project/fighting_game_bot%20-%20ratatui/dist/Idolshowdown_autobot.exe) để mở chương trình với giao diện TUI.
3. Các file dữ liệu cấu hình như `config.json` và `combos.json` sẽ tự động được khởi tạo ngay tại thư mục chứa file `.exe` này nếu chưa tồn tại.

### Cách 2: Khởi chạy bằng Python Launcher
Nếu bạn muốn chạy thông qua tệp khởi động Python:
1. Chạy lệnh:
   ```powershell
   python run.py
   ```
2. Trình khởi động sẽ tự động khởi động backend Flask ngầm và chạy giao diện TUI Rust phía trên để bạn sử dụng.

---

## 📝 Giấy Phép & Lưu Ý
* Phần mềm phát triển phục vụ mục đích học tập nghiên cứu cơ chế mô phỏng phím bấm của Windows API.
* **Lưu ý**: Hãy chạy trò chơi ở chế độ cửa sổ (Windowed Mode) hoặc Click chuột active vào cửa sổ game trước khi kích hoạt combo để phím bấm ảo được ghi nhận chính xác.
