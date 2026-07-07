import psutil
import pygetwindow as gw

class GameMonitor:
    """
    Manages and monitors the game process and window focus state.
    Ensures that inputs are only simulated when the target game is running and focused.
    """
    def __init__(self, process_name: str, window_title: str):
        """
        Initializes the GameMonitor with target process name and window title.
        
        :param process_name: Name of the game executable (e.g., 'notepad.exe' or 'notepad')
        :param window_title: Substring of the target window title to match (e.g., 'Notepad')
        """
        self.process_name = process_name
        self.window_title = window_title

    def is_game_running(self, process_name: str = None) -> bool:
        """
        Checks if the game process is running in the system using psutil.
        
        :param process_name: Optional override for the process name.
        :return: True if the process is running, False otherwise.
        """
        target = (process_name or self.process_name).lower()
        try:
            # Iterate through all active processes
            for proc in psutil.process_iter(['name']):
                name = proc.info['name']
                if name:
                    name_lower = name.lower()
                    # Check for exact match or match adding '.exe' extension
                    if name_lower == target or name_lower == f"{target}.exe":
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            print(f"[GameMonitor Error] Error checking process: {e}")
        return False

    def is_game_focused(self, window_title: str = None) -> bool:
        """
        Checks if the target window is currently focused (active) using pygetwindow.
        
        :param window_title: Optional override for the window title.
        :return: True if the window is active/focused, False otherwise.
        """
        target = (window_title or self.window_title).lower()
        try:
            active_window = gw.getActiveWindow()
            if active_window is None:
                return False
            # Check if target window title is a substring of the active window title
            return target in active_window.title.lower()
        except Exception as e:
            # Standard error handling to avoid crash if some windows return error when queried
            return False

    def check_fail_safe(self, process_name: str = None, window_title: str = None) -> bool:
        """
        Utility method to perform both running and focus checks.
        
        :return: True if the game is running and focused, False otherwise.
        """
        p_name = process_name or self.process_name
        w_title = window_title or self.window_title
        
        # Game must be running
        if not self.is_game_running(p_name):
            return False
            
        # Game must be focused
        if not self.is_game_focused(w_title):
            return False
            
        return True
