import ctypes
from ctypes import wintypes
import threading
from typing import Callable

# Windows API Constants
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000

# Virtual Key Codes (VK) Mapper
def get_vk_code(key_name: str) -> int:
    key_name = key_name.lower().strip()
    
    # Function keys: F1 to F24
    if key_name.startswith("f") and key_name[1:].isdigit():
        f_num = int(key_name[1:])
        if 1 <= f_num <= 24:
            return 0x6F + f_num
            
    # Letters A to Z
    if len(key_name) == 1 and 'a' <= key_name <= 'z':
        return ord(key_name.upper())
        
    # Numbers 0 to 9
    if len(key_name) == 1 and '0' <= key_name <= '9':
        return ord(key_name)
        
    # Special keys
    special_keys = {
        "backspace": 0x08,
        "tab": 0x09,
        "clear": 0x0C,
        "enter": 0x0D,
        "return": 0x0D,
        "shift": 0x10,
        "ctrl": 0x11,
        "control": 0x11,
        "alt": 0x12,
        "pause": 0x13,
        "capslock": 0x14,
        "caps_lock": 0x14,
        "escape": 0x1B,
        "esc": 0x1B,
        "space": 0x20,
        "pageup": 0x21,
        "page_up": 0x21,
        "pagedown": 0x22,
        "page_down": 0x22,
        "end": 0x23,
        "home": 0x24,
        "left": 0x25,
        "up": 0x26,
        "right": 0x27,
        "down": 0x28,
        "select": 0x29,
        "print": 0x2A,
        "execute": 0x2B,
        "snapshot": 0x2C,
        "printscreen": 0x2C,
        "insert": 0x2D,
        "delete": 0x2E,
        "help": 0x2F,
        "numlock": 0x90,
        "num_lock": 0x90,
        "scrolllock": 0x91,
        "scroll_lock": 0x91,
    }
    
    return special_keys.get(key_name)

class WindowsHotkeyListener:
    """Listens for global Windows hotkeys using RegisterHotKey API in a background thread.
    Requires no external packages (pure Python/ctypes).
    """
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self._hotkeys = {}
        self._thread = None
        self._running = False

    def register_hotkey(self, key_name: str, callback: Callable[[], None]):
        """Saves a hotkey mapping to be registered when the listener starts."""
        key_name = key_name.lower().strip()
        vk_code = get_vk_code(key_name)
        if not vk_code:
            raise ValueError(f"Unsupported hotkey: {key_name}.")
        
        # Use the vk_code as the unique hotkey ID
        self._hotkeys[vk_code] = {
            "vk": vk_code,
            "callback": callback,
            "name": key_name
        }

    def _loop(self):
        # Register all hotkeys in this thread's context
        for hotkey_id, hk in self._hotkeys.items():
            success = self.user32.RegisterHotKey(
                None,          # NULL means associate with this thread
                hotkey_id,     # ID of the hotkey
                MOD_NOREPEAT,  # Modifiers (no repeat on hold)
                hk["vk"]       # Virtual Key
            )
            if success:
                print(f"[Hotkey] Registered {hk['name'].upper()} successfully.")
            else:
                print(f"[Hotkey] Failed to register {hk['name'].upper()}. Error code: {ctypes.GetLastError()}")

        self._running = True
        
        try:
            msg = wintypes.MSG()
            # GetMessage blocks until a message arrives
            while self._running and self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    if hotkey_id in self._hotkeys:
                        hk_name = self._hotkeys[hotkey_id]["name"].upper()
                        print(f"[Hotkey Debug] Hotkey {hk_name} message received!")
                        # Invoke callback on a separate thread so it doesn't block the message loop
                        threading.Thread(target=self._hotkeys[hotkey_id]["callback"], daemon=True).start()
                        
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            # Unregister hotkeys when loop terminates
            for hotkey_id in self._hotkeys.keys():
                self.user32.UnregisterHotKey(None, hotkey_id)
            print("[Hotkey] Unregistered all hotkeys.")

    def start(self):
        """Starts listening for hotkeys in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops listening for hotkeys."""
        self._running = False
        # Post a dummy WM_NULL message to wake up GetMessage loop and exit
        self.user32.PostThreadMessageW(self._thread.ident, 0, 0, 0)
