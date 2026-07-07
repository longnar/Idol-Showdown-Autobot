import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import direct_input
    import sequence
    import controller
    import hotkey
    import config
    
    print("[Test] All modules imported successfully!")
    
    # Test window titles check
    ctrl = controller.FightingGameController([], "Notepad")
    active_title = ctrl.get_active_window_title()
    print(f"[Test] Active window title: '{active_title}'")
    print(f"[Test] Is active window focused? {ctrl.is_game_focused()}")
    
    print("[Test] Verification script completed with no errors.")
    sys.exit(0)
except Exception as e:
    print(f"[Error] Verification failed: {e}")
    sys.exit(1)
