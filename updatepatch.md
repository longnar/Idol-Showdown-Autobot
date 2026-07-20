# Update Patch Log

This document lists all major patches, bug fixes, UX enhancements, and structural changes implemented in the Fighting Game Autobot system.

---

## 1. Spelling Corrections
*   **Action Mapping Typo**: Fixed the typo where the key event mapping for `Grab` was registered as `GRAP` instead of `GRAB`.
*   **Parser & Validator Cleaning**: Completely removed references to `GRAP` in `input_mapper.py`, `combo_playlist_manager.py`, and `app.py`. The system now correctly expects and processes `GRAB`.

## 2. User Experience (UX) Enhancements
*   **Console Log Auto-Scroll**: Improved the real-time logging panel (`SystemLogsPanel.jsx`) by adding an automatic scrolling script that moves the viewport to the newest log entry whenever the logs buffer is updated.
*   **Clean Layout & Spacing**: Standardized panel margins and added clear layout structures for options cards to optimize visibility on compact displays (1280x720).

## 3. Playlist & Database Logic Upgrades
*   **First Run Initialization**:
    *   If `playlists.json` does not exist or is empty, the system marks the state as `first_run`.
    *   On a `first_run`, the app initializes a clean playlist structure `{"default": []}` and automatically resets the combos database (`combos.json` is set to `[]`), guaranteeing a clean, empty UI for new users instead of loading residual test records.
*   **Dynamic Playlist Sync & Validation**:
    *   Added the `load_and_select_playlist(playlist_name)` utility.
    *   The utility reloads `playlists.json` from disk before selecting a playlist and checks if the chosen target exists. If it does not exist, it falls back to a safe fallback (the first available playlist or a default clean list) to avoid crashes.

## 4. Architectural & Automation Improvements
*   **Dynamic Process & Window Monitoring**:
    *   Removed all hardcoded process names ("notepad.exe") and window titles ("Notepad") from config templates and class defaults.
    *   Refactored `GameMonitor` to use dynamic properties that query the configuration manager directly. Checking active status now queries live configuration values from `config.json` rather than static fields.
*   **Elimination of Auto-Select Dropdown**:
    *   Removed the automatic active window list selector dropdown and its `/api/active_windows` backend endpoint to simplify configuration. Users manually enter their game's exact process and window name.
*   **Global Hotkey Fixes & Event Logging**:
    *   Replaced the limited F1-F12 hotkey lookup map with a dynamic `get_vk_code(key_name)` mapping function that parses alphanumeric keys, function keys (F1-F24), and special keys (Ctrl, Alt, Shift, Enter, Space, etc.) using Windows virtual key codes.
    *   Added a debug print inside `WindowsHotkeyListener`'s message loop (`[Hotkey Debug] Hotkey {hk_name} message received!`) to trace hotkeys in the console.
    *   Implemented `toggle_bot` in `app.py`'s `BotManager` to capture start/stop signals and log their dispatch.
    *   Updated the CLI `main.py` script to fetch hotkeys dynamically from the user's config file instead of hardcoded constants.
*   **Thread & State Self-Healing**:
    *   Added an `is_running` check to `PlaylistOrchestrator` to query if the worker thread is active.
    *   Updated the `/api/bot/status` endpoint to check if the thread is alive, self-healing the state (`running = False`) if the background thread has terminated or aborted.

## 5. Bản vá cải tiến nâng cao & Trình phân tích Combo chuyên sâu (Mới nhất)
*   **Cuộn Console Log thông minh (Smart Auto-scroll)**: Cập nhật component `SystemLogsPanel.jsx` để tránh làm phiền khi người dùng đang kiểm tra log cũ. Khung log chỉ tự động cuộn xuống khi người dùng đang ở đáy màn hình console, ngược lại sẽ giữ nguyên vị trí cuộn.
*   **Mở rộng bộ ký hiệu Combo (Fighting Game Notation)**: 
    *   Hỗ trợ ký hiệu Kara Cancel (`X~Y`) tự động chuyển thành cancel nhanh.
    *   Hỗ trợ sạc/giữ đòn với bracket `[X]` (giữ nút, thêm 30 frames) và `{X}` (sạc đòn, thêm 15 frames) để điều khiển thời gian nhấn phím chính xác.
    *   Hỗ trợ phím bổ trợ, đòn tùy chọn `(X)`, lựa chọn đòn `X/Y`, Superchat Cancel (`scc` chuyển thành cancel `>`).
    *   Nhận diện các ký hiệu airborne (`j.`), delay (`dl.`), microdash (`md.`), và các chú thích như `CH`, `OTG`, hitcount `X(n)`.
    *   **Vá lỗi & Tự động Nhảy cho đòn trên không (`j.X`)**: Chuyển đổi xử lý tiền tố `j.` từ dạng nhận diện tĩnh sang thực thi động. Khi phát hiện `j.X` (như `j.H` hoặc `j.214L`), hệ thống sẽ phân tích trạng thái nhân vật: nếu chưa nhảy, hệ thống tự động chèn lệnh nhảy `Jump (Up)` cùng một khoảng delay ngắn để nhân vật rời đất trước khi tung đòn, đồng thời ghi log chi tiết từng bước phân tích ra ô `Testing input notice`.
    *   **Nâng cấp Combo Parser chuyên sâu**: Hỗ trợ đầy đủ các chuỗi combo chuỗi dài phức tạp kết hợp đồng thời nhiều toán tử hủy đòn (`~`, `>`), hướng di chuyển đa đòn liên tục (`214L`, `22L`, `3H`), và đòn nhảy trên không có dấu chấm (`j.214L`, `j.H`).
*   **Báo lỗi cú pháp chi tiết (Detailed Exception Handling)**: Thay thế cơ chế validate cũ bằng việc chạy thử nghiệm dry-run thông qua `InputMapper`. Nếu phát hiện ký tự hoặc đòn đánh lạ không hợp lệ, hệ thống sẽ quăng ngoại lệ chỉ ra chính xác ký tự/đoạn bị lỗi (ví dụ: chỉ rõ ký tự lỗi nằm trong token nào) hiển thị trực tiếp lên ô `Testing input notice`.
*   **Đồng bộ kiểm thử Combo (Test Combo Fix)**: Chuyển đổi endpoint `/api/test_combo` sang chạy đồng bộ kết nối thông tin phản hồi từ backend. Kết quả thực thi cuối cùng (thành công hoặc lỗi mất focus/không hoạt động) sẽ được cập nhật trực tiếp tại khung `Testing input notice`.
*   **Giả lập hướng di chuyển phím số**: Cập nhật module `direct_input.py` để nhận diện các nút di chuyển đơn lẻ dạng numpad notation từ `1`-`9` và tự động ánh xạ thành tổ hợp các phím di chuyển tương ứng (`w`, `a`, `s`, `d`) lấy từ file cấu hình của người dùng.
