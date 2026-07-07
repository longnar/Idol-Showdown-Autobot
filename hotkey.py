import ctypes
from ctypes import wintypes
import threading
from typing import Callable

# Windows API Constants
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000

# Virtual Key Codes (VK)
# F1 to F12 are 0x70 to 0x7B
VK_MAP = {
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
    "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "num_lock": 0x90, "scroll_lock": 0x91,
}

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
        key_name = key_name.lower()
        if key_name not in VK_MAP:
            raise ValueError(f"Unsupported hotkey: {key_name}. Supported keys: F1-F12")
        
        vk_code = VK_MAP[key_name]
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
