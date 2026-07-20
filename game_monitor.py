import time
import psutil
# pyrefly: ignore [missing-import]
import pygetwindow as gw

class GameMonitor:
    """
    Manages and monitors the game process and window focus state.
    Ensures that inputs are only simulated when the target game is running and focused.
    Optimized for low CPU overhead on low-end configurations via cache management.
    """
    # Class-level caching and interaction tracking variables
    _process_cache = {}  # Key: target_process_name_lower, Value: (is_running, pid, last_check_time)
    _focus_cache = {}    # Key: target_window_title_lower, Value: (is_focused, last_check_time)
    _last_interaction_time = time.time()

    @classmethod
    def update_interaction(cls):
        """Updates the timestamp of the last user interaction."""
        cls._last_interaction_time = time.time()

    @property
    def bot_running(self) -> bool:
        """Dynamically queries the bot manager running state in a circular-import safe manner."""
        try:
            import sys
            if 'app' in sys.modules:
                app_module = sys.modules['app']
                if hasattr(app_module, 'bot_mgr'):
                    return app_module.bot_mgr.running
        except Exception:
            pass
        return False

    def get_cache_durations(self):
        """
        Determines the cache expiry limits.
        If active (bot running or user interaction in last 5s), checks process every 1.0s and focus every 0.25s.
        If idle, checks process every 5.0s and focus every 2.0s to minimize CPU usage.
        """
        if self.bot_running or (time.time() - self._last_interaction_time < 5.0):
            return 1.0, 0.25
        else:
            return 5.0, 2.0

    @staticmethod
    def get_active_windows():
        """
        Enumerates all active windows and grabs their window title and process executable name.
        Uses ctypes to query process ID from HWND.
        """
        import ctypes
        import psutil
        import pygetwindow as gw
        
        windows_info = []
        seen_titles = set()
        
        try:
            all_windows = gw.getAllWindows()
            for w in all_windows:
                title = w.title.strip()
                if not title:
                    continue
                if title in seen_titles:
                    continue
                    
                hwnd = w._hWnd
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                process_name = "unknown.exe"
                if pid.value > 0:
                    try:
                        proc = psutil.Process(pid.value)
                        process_name = proc.name()
                    except Exception:
                        pass
                        
                windows_info.append({
                    "title": title,
                    "process": process_name
                })
                seen_titles.add(title)
        except Exception as e:
            print(f"[GameMonitor Error] Error listing windows: {e}")
            
        windows_info.sort(key=lambda x: x["title"].lower())
        return windows_info

    def __init__(self, config_manager=None, process_name: str = None, window_title: str = None):
        self.config_manager = config_manager
        self._process_name = process_name
        self._window_title = window_title

    @property
    def process_name(self) -> str:
        if self.config_manager:
            return self.config_manager.config.get("game_process", "")
        if not self._process_name:
            import os, json
            if os.path.exists("config.json"):
                try:
                    with open("config.json", "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        return cfg.get("game_process", "")
                except Exception:
                    pass
        return self._process_name or ""

    @property
    def window_title(self) -> str:
        if self.config_manager:
            return self.config_manager.config.get("game_window", "")
        if not self._window_title:
            import os, json
            if os.path.exists("config.json"):
                try:
                    with open("config.json", "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        return cfg.get("game_window", "")
                except Exception:
                    pass
        return self._window_title or ""

    def is_game_running(self, process_name: str = None) -> bool:
        """
        Checks if the game process is running. Uses process list cache to reduce CPU load.
        """
        target = (process_name or self.process_name).lower()
        now = time.time()
        process_expiry, _ = self.get_cache_durations()
        
        # Check cache
        if target in self._process_cache:
            is_running, pid, timestamp = self._process_cache[target]
            if now - timestamp < process_expiry:
                return is_running
                
        # Cache miss or expired - perform scanning
        is_running = False
        pid = None
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                name = proc.info['name']
                if name:
                    name_lower = name.lower()
                    if name_lower == target or name_lower == f"{target}.exe":
                        is_running = True
                        pid = proc.info['pid']
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            print(f"[GameMonitor Error] Error checking process: {e}")
            
        # Update cache
        self._process_cache[target] = (is_running, pid, now)
        return is_running

    def get_game_pid(self, process_name: str = None):
        """
        Gets the PID of the game process. Uses process list cache.
        """
        target = (process_name or self.process_name).lower()
        now = time.time()
        process_expiry, _ = self.get_cache_durations()
        
        # Check cache
        if target in self._process_cache:
            is_running, pid, timestamp = self._process_cache[target]
            if now - timestamp < process_expiry:
                return pid
                
        # Cache miss or expired - trigger is_game_running to populate cache
        self.is_game_running(target)
        return self._process_cache.get(target, (False, None, 0))[1]

    def is_game_focused(self, window_title: str = None) -> bool:
        """
        Checks if the target window is focused. Uses foreground window cache to reduce CPU.
        """
        target = (window_title or self.window_title).lower()
        now = time.time()
        _, focus_expiry = self.get_cache_durations()
        
        # Check cache
        if target in self._focus_cache:
            is_focused, timestamp = self._focus_cache[target]
            if now - timestamp < focus_expiry:
                return is_focused
                
        # Cache miss or expired - check active window
        is_focused = False
        try:
            active_window = gw.getActiveWindow()
            if active_window is not None:
                is_focused = target in active_window.title.lower()
        except Exception:
            pass
            
        # Update cache
        self._focus_cache[target] = (is_focused, now)
        return is_focused

    def check_fail_safe(self, process_name: str = None, window_title: str = None) -> bool:
        """
        Utility fail-safe check.
        """
        p_name = process_name or self.process_name
        w_title = window_title or self.window_title
        
        if not self.is_game_running(p_name):
            return False
            
        if not self.is_game_focused(w_title):
            return False
            
        return True
