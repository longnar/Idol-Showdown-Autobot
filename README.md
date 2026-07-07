# Idol Showdown Autobot - Phiên bản V0.1 (Beta)

Chào mừng bạn đến với **Idol Showdown Autobot (V0.1 Beta)**, một ứng dụng desktop mạnh mẽ giúp tự động hóa chuỗi combo và di chuyển đòn đánh cho người chơi số 2 (Player 2) trong tựa game đối kháng Idol Showdown. 

Ứng dụng được xây dựng trên mô hình kết hợp giữa **Backend Python (Flask + PyWebView)** và **Frontend React (Vite + Tailwind CSS)** để tạo ra một phần mềm desktop hoàn chỉnh, độc lập và không phụ thuộc vào dòng lệnh đen của Windows.

---

## 🌟 Các Tính Năng Nổi Bật

*   🖥️ **Giao diện Desktop độc lập**: Chạy dưới dạng cửa sổ độc lập kích thước cố định **1280x720** bằng PyWebView. Không hiển thị cửa sổ console màu đen.
*   ⌨️ **Lắng nghe phím tắt toàn cục (Global Hotkeys)**: Nhấn `F9` để Bắt đầu chạy playlist bot và `F10` để Tạm dừng ngay lập tức thông qua Windows Message Loop ngầm.
*   ⚡ **Bộ phân tích Combo tối ưu (Smart Parser)**:
    *   **Phím gộp (`"+"`)**: Thực hiện nhấn các phím ảo cùng một thời điểm (ví dụ: `2+H`, `L+M`).
    *   **Cancel nhanh (`">"`)**: Chuyển đổi đòn đánh ngay lập tức sau **5 frames** (~0.08 giây) giúp chuỗi Gatling/Combo không bị rụng giữa chừng.
    *   **Chờ nhịp (`","`)**: Tạo khoảng trễ giữa các khối đòn đánh bằng đúng số frames thiết lập trong cấu hình `delay_frames` trên giao diện.
*   🔄 **Hỗ trợ đảo hướng phím bấm (Player 2 Side)**: Tự động đổi hướng phím di chuyển (Trái/Phải, Tiến/Lùi) dựa theo vị trí của Player 2 trên sân đấu (Bên phải hướng sang trái hoặc Bên trái hướng sang phải).
*   📁 **Quản lý Playlist & Combo trực quan**: Tạo, chỉnh sửa, xóa combo và gán chúng vào các Playlist cấu hình khác nhau trực tiếp trên giao diện UI.
*   🩺 **Bảng giám sát Logs thời gian thực**: Theo dõi từng phím nhấn ảo được thi triển lên trò chơi trực tiếp tại giao diện Diagnostics.

---

## 🚀 Hướng Dẫn Vận Hành

### Cách 1: Chạy trực tiếp từ File Thực thi (.exe)
1.  Truy cập thư mục [dist/](file:///l:/Code%20Project/fighting_game_bot/dist/).
2.  Nhấp đúp chuột vào tệp [Idolshowdown_autobot.exe](file:///l:/Code%20Project/fighting_game_bot/dist/Idolshowdown_autobot.exe) để mở chương trình dưới dạng Desktop App.
3.  Các file dữ liệu cấu hình như `config.json` và `combos.json` sẽ tự động được khởi tạo ngay tại thư mục chứa file `.exe` này.

### Cách 2: Chạy từ Mã nguồn (Dành cho nhà phát triển)
Đảm bảo bạn đã có **Python 3.10+** và **Node.js** cài đặt trên Windows.

1.  **Cài đặt thư viện Python**:
    ```powershell
    .venv\Scripts\pip install -r requirements.txt
    .venv\Scripts\pip install flask pywebview pyinstaller
    ```
2.  **Biên dịch Frontend React**:
    ```powershell
    cd gui
    npm install
    npm run build
    cd ..
    ```
3.  **Khởi chạy ứng dụng**:
    ```powershell
    .venv\Scripts\python run.py
    ```

---

## 🛠️ Hướng Dẫn Đóng Gói Lại Ứng Dụng

Nếu bạn thay đổi mã nguồn Python hoặc giao diện React và muốn xuất lại tệp `.exe` độc lập:

```powershell
.venv\Scripts\pyinstaller --onefile --windowed --name=Idolshowdown_autobot --add-data "gui/dist;gui/dist" run.py
```

---

## 📤 Hướng Dẫn Đưa Dự Án Lên GitHub

Chúng tôi đã cấu hình sẵn tệp `.gitignore` để loại bỏ các thư mục rác, thư mục ảo `.venv` và `node_modules` nặng nề khi đưa lên GitHub. Hãy thực hiện các lệnh sau trong Terminal tại thư mục gốc:

1.  **Khởi tạo Git**:
    ```powershell
    git init
    ```
2.  **Thêm các tệp vào tracking**:
    ```powershell
    git add .
    ```
3.  **Commit phiên bản Beta đầu tiên**:
    ```powershell
    git commit -m "Initial commit V0.1 Beta - Integrated PyWebView Desktop App"
    ```
4.  **Tạo Repository mới trên GitHub**, sau đó chạy các lệnh liên kết (thay thế URL bằng link repo của bạn):
    ```powershell
    git branch -M main
    git remote add origin https://github.com/ten-user-cua-ban/ten-repo-cua-ban.git
    git push -u origin main
    ```

---

## 📝 Giấy Phép & Lưu Ý
*   Phần mềm phát triển phục vụ mục đích học tập nghiên cứu cơ chế mô phỏng phím bấm của Windows API.
*   **Lưu ý**: Hãy chạy trò chơi ở chế độ cửa sổ (Windowed Mode) hoặc Click chuột active vào cửa sổ game trước khi kích hoạt combo để phím bấm ảo được ghi nhận chính xác.
