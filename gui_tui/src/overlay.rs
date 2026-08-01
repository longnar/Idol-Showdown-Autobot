use std::sync::{Arc, Mutex};
use std::thread;
use std::ptr;
use windows_sys::Win32::Foundation::*;
use windows_sys::Win32::Graphics::Gdi::*;
use windows_sys::Win32::UI::WindowsAndMessaging::*;
use windows_sys::Win32::System::LibraryLoader::GetModuleHandleW;

// Thread-safe wrapper for HWND
#[derive(Clone, Copy)]
struct SafeHwnd(HWND);
unsafe impl Send for SafeHwnd {}
unsafe impl Sync for SafeHwnd {}

// Shared state for the window text
lazy_static::lazy_static! {
    static ref OVERLAY_TEXT: Arc<Mutex<String>> = Arc::new(Mutex::new(String::new()));
}

pub struct OverlayController {
    hwnd: SafeHwnd,
}

impl OverlayController {
    pub fn new() -> Self {
        let (tx, rx) = std::sync::mpsc::channel();

        // Run the window message loop on a separate thread
        thread::spawn(move || {
            unsafe {
                let hinstance = GetModuleHandleW(ptr::null());
                let class_name = to_wide("AutobotOverlayClass");

                let wnd_class = WNDCLASSW {
                    style: CS_HREDRAW | CS_VREDRAW,
                    lpfnWndProc: Some(wnd_proc),
                    cbClsExtra: 0,
                    cbWndExtra: 0,
                    hInstance: hinstance,
                    hIcon: 0,
                    hCursor: LoadCursorW(0, IDC_ARROW as *const u16),
                    hbrBackground: CreateSolidBrush(0x00000000), // Black background for colorkey transparency
                    lpszMenuName: ptr::null(),
                    lpszClassName: class_name.as_ptr(),
                };

                RegisterClassW(&wnd_class);

                // Get screen dimensions to center the overlay near the top/bottom
                let screen_width = GetSystemMetrics(SM_CXSCREEN);
                let screen_height = GetSystemMetrics(SM_CYSCREEN);

                // Width: 800px, Height: 70px, Positioned at the bottom middle of the screen
                let width = 800;
                let height = 80;
                let x = (screen_width - width) / 2;
                let y = screen_height - height - 120; // 120px from bottom

                // Create overlay window with WS_EX_TOPMOST, WS_EX_TRANSPARENT (click-through), WS_EX_LAYERED (translucent/colorkey), WS_EX_TOOLWINDOW (no taskbar icon)
                let hwnd = CreateWindowExW(
                    WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW,
                    class_name.as_ptr(),
                    to_wide("Idol Showdown Combo Overlay").as_ptr(),
                    WS_POPUP,
                    x,
                    y,
                    width,
                    height,
                    0,
                    0,
                    hinstance,
                    ptr::null(),
                );

                if hwnd == 0 {
                    let _ = tx.send(Err("Failed to create overlay window"));
                    return;
                }

                // Set black (0x00000000) as the transparent colorkey. 
                // Any pixel drawn black will be fully transparent (see-through to the game), while colored text will remain solid.
                SetLayeredWindowAttributes(hwnd, 0x00000000, 0, LWA_COLORKEY);

                let _ = tx.send(Ok(SafeHwnd(hwnd)));

                // Start message loop
                let mut msg: MSG = std::mem::zeroed();
                while GetMessageW(&mut msg, 0, 0, 0) > 0 {
                    TranslateMessage(&mut msg);
                    DispatchMessageW(&mut msg);
                }
            }
        });

        let hwnd = rx.recv().unwrap().expect("Overlay creation failed");

        Self { hwnd }
    }

    pub fn set_text(&self, text: &str) {
        if let Ok(mut guard) = OVERLAY_TEXT.lock() {
            *guard = text.to_string();
        }
        unsafe {
            // Trigger repaint on the overlay window
            InvalidateRect(self.hwnd.0, ptr::null(), TRUE);
        }
    }

    pub fn show(&self) {
        unsafe {
            ShowWindow(self.hwnd.0, SW_SHOW);
            // Force the window to be top-most again just in case
            SetWindowPos(self.hwnd.0, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
        }
    }

    pub fn hide(&self) {
        unsafe {
            ShowWindow(self.hwnd.0, SW_HIDE);
        }
    }

    pub fn close(self) {
        unsafe {
            PostMessageW(self.hwnd.0, WM_CLOSE, 0, 0);
        }
    }
}

// Window Procedure for Overlay
unsafe extern "system" fn wnd_proc(hwnd: HWND, msg: u32, wparam: WPARAM, lparam: LPARAM) -> LRESULT {
    match msg {
        WM_PAINT => {
            let mut ps: PAINTSTRUCT = std::mem::zeroed();
            let hdc = BeginPaint(hwnd, &mut ps);

            // Fetch the current text
            let text = if let Ok(guard) = OVERLAY_TEXT.lock() {
                guard.clone()
            } else {
                String::new()
            };

            // Get window client size
            let mut rect: RECT = std::mem::zeroed();
            GetClientRect(hwnd, &mut rect);

            // Fill background with black brush (so it triggers LWA_COLORKEY transparency)
            let brush = CreateSolidBrush(0x00000000);
            FillRect(hdc, &rect, brush);
            DeleteObject(brush);

            // Select a nice large clean font
            let font = CreateFontW(
                32,                          // Height
                0,                           // Width
                0, 0,                        // Angles
                FW_BOLD as i32,              // Weight (Bold)
                0, 0, 0,                     // Italic, Underline, Strikeout
                DEFAULT_CHARSET as u32,
                OUT_DEFAULT_PRECIS as u32,
                CLIP_DEFAULT_PRECIS as u32,
                CLEARTYPE_QUALITY as u32,
                DEFAULT_PITCH as u32 | FF_DONTCARE as u32,
                to_wide("Consolas").as_ptr(),
            );
            let old_font = SelectObject(hdc, font);

            // Draw outer border (Subtle dark background bar for readability)
            // Draw a rounded rectangle for a smooth dark pill layout
            let bg_brush = CreateSolidBrush(0x00111111); // Dark charcoal, slightly offset from black so it's translucent rather than fully invisible
            let pen = CreatePen(PS_SOLID as i32, 2, 0x0000FFFF); // Cyan border
            let old_brush = SelectObject(hdc, bg_brush);
            let old_pen = SelectObject(hdc, pen);
            
            // Draw a pill bar
            RoundRect(hdc, rect.left + 5, rect.top + 5, rect.right - 5, rect.bottom - 5, 25, 25);
            
            SelectObject(hdc, old_brush);
            SelectObject(hdc, old_pen);
            DeleteObject(bg_brush);
            DeleteObject(pen);

            // Set Text rendering options
            SetBkMode(hdc, TRANSPARENT as i32);
            
            // Render "RECORDING COMBO" prefix in bright red
            SetTextColor(hdc, 0x000000FF); // Red (BGR format: 0x00BBGGRR)
            let prefix = to_wide("● RECORDING: ");
            let mut prefix_rect = rect;
            prefix_rect.left += 30;
            prefix_rect.top += 18;
            DrawTextW(hdc, prefix.as_ptr(), -1, &mut prefix_rect, DT_LEFT | DT_SINGLELINE);

            // Offset the rest of the text
            let mut text_rect = rect;
            text_rect.left += 230; // Shift right of the recording dot
            text_rect.top += 18;
            
            if text.is_empty() {
                SetTextColor(hdc, 0x00888888); // Gray
                let placeholder = to_wide("Press game keys (e.g. 236H > 5L)...");
                DrawTextW(hdc, placeholder.as_ptr(), -1, &mut text_rect, DT_LEFT | DT_SINGLELINE);
            } else {
                SetTextColor(hdc, 0x00FFFF00); // Yellow/Cyan (0x00FFFF00 is Cyan/Yellow depending on BGR format)
                let display_text = if text.chars().count() > 30 {
                    let skip_count = text.chars().count() - 26;
                    format!("... {}", text.chars().skip(skip_count).collect::<String>())
                } else {
                    text.clone()
                };
                let wide_text = to_wide(&display_text);
                DrawTextW(hdc, wide_text.as_ptr(), -1, &mut text_rect, DT_LEFT | DT_SINGLELINE);
            }

            // Cleanup
            SelectObject(hdc, old_font);
            DeleteObject(font);

            EndPaint(hwnd, &ps);
            0
        }
        WM_DESTROY => {
            PostQuitMessage(0);
            0
        }
        _ => DefWindowProcW(hwnd, msg, wparam, lparam),
    }
}

// Convert Rust str to wide UTF-16 string (null terminated)
fn to_wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}
