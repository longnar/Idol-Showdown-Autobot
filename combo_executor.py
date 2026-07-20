import time
import random
from typing import List
from config_manager import ConfigManager
from game_monitor import GameMonitor
from direct_input import press_key, release_key, SCAN_CODES

class ComboExecutor:
    """
    Parses and executes action combo sequences (e.g. 'Down, Forward, Attack').
    Converts action names to keys based on configuration and simulates input into the game.
    Features a low-latency fail-safe mechanism using GameMonitor to stop input if focus is lost.
    """
    def __init__(self, config_manager: ConfigManager, game_monitor: GameMonitor, fps: float = 60.0):
        """
        Initializes the ComboExecutor.
        
        :param config_manager: ConfigManager instance to fetch current key bindings.
        :param game_monitor: GameMonitor instance to check game active status.
        :param fps: Configured target game frame rate (default: 60.0).
        """
        self.config_manager = config_manager
        self.game_monitor = game_monitor
        self.fps = fps

    def release_all_keys(self):
        """
        Safety function to release all defined keys to prevent them from getting stuck.
        """
        for key in SCAN_CODES.keys():
            release_key(key)

    def reset_executor_state(self):
        """
        Resets the executor state by releasing all virtual keys completely.
        """
        self.release_all_keys()

    def sleep_with_fail_safe(self, duration_sec: float) -> bool:
        """
        High-resolution sleep that polls the GameMonitor at low latency (50ms).
        If the game closes or loses focus, it immediately releases keys and aborts.
        
        :param duration_sec: Duration to sleep in seconds.
        :return: True if the sleep finished safely, False if aborted by fail-safe.
        """
        start_time = time.perf_counter()
        poll_interval_sec = 0.05 # 50 ms polling interval (approx. 3 frames at 60 FPS)
        
        while time.perf_counter() - start_time < duration_sec:
            # Low-latency polling check
            if not self.game_monitor.check_fail_safe():
                print("\n[Fail-safe Triggered] Game is no longer running or focused! Aborting input execution immediately.")
                self.release_all_keys()
                return False
            
            # Compute remaining time to sleep
            elapsed = time.perf_counter() - start_time
            remaining = duration_sec - elapsed
            
            # Sleep in a small slice
            sleep_slice = min(poll_interval_sec, remaining)
            if sleep_slice > 0:
                time.sleep(sleep_slice)
                
        return True

    def execute_overlapping_combo(self, key_events: List[dict]) -> bool:
        """
        Executes a list of time-based key hold objects using a background scheduler thread.
        Each event object is: {"key": str, "start_time": float, "hold_duration": float}
        
        Ensures keys are held in parallel (overlapping) and that presses always happen
        before releases when scheduled at the same timestamp.
        """
        if not key_events:
            print("[ComboExecutor Error] No key events to execute.")
            return False
            
        import threading
        
        # 1. Compile events timeline
        timeline = []
        for obj in key_events:
            key = obj["key"]
            start = obj["start_time"]
            duration = obj["hold_duration"]
            
            timeline.append({"time": start, "type": "press", "key": key})
            timeline.append({"time": start + duration, "type": "release", "key": key})
            
        # Sort events: primary sorting by time, secondary sorting so 'press' comes before 'release'
        timeline.sort(key=lambda x: (x["time"], 0 if x["type"] == "press" else 1))
        
        # Thread communication flag
        abort_event = threading.Event()
        
        def scheduler():
            try:
                # Initial safety check
                if not self.game_monitor.check_fail_safe():
                    print("[ComboExecutor Warning] Cannot start combo: Game is not running or focused.")
                    abort_event.set()
                    return
                    
                print(f"[ComboExecutor] Starting overlapping hold execution ({len(key_events)} events)...")
                start_time = time.perf_counter()
                
                for idx, event in enumerate(timeline):
                    if abort_event.is_set():
                        break
                        
                    target_time = start_time + event["time"]
                    
                    # High-precision wait with fail-safe polling (every 10ms)
                    while time.perf_counter() < target_time:
                        if not self.game_monitor.check_fail_safe():
                            print("\n[Fail-safe Triggered] Game is no longer running or focused! Aborting execution.")
                            abort_event.set()
                            break
                        # Sleep in tiny increments to keep CPU free and maintain focus checks
                        sleep_time = min(0.01, target_time - time.perf_counter())
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                            
                    if abort_event.is_set():
                        break
                        
                    # Execute event
                    key = event["key"]
                    if event["type"] == "press":
                        press_key(key)
                    else:
                        release_key(key)
                        
                if not abort_event.is_set():
                    print("[ComboExecutor] Overlapping combo executed successfully!")
            except Exception as e:
                print(f"[ComboExecutor Error] Error during execution: {e}")
                abort_event.set()
            finally:
                # Always release all keys at the end of execution
                self.release_all_keys()
                
        # Launch scheduler thread
        scheduler_thread = threading.Thread(target=scheduler, daemon=True)
        scheduler_thread.start()
        
        # Block until the scheduler completes to maintain CLI menu flow
        scheduler_thread.join()
        
        return not abort_event.is_set()

    def execute_combo(self, combo_sequence_str: str) -> bool:
        """
        Convenience wrapper to parse and execute an action-name combo.
        
        :param combo_sequence_str: E.g., 'Down, Forward, Light'
        :return: True if executed successfully, False otherwise.
        """
        from input_mapper import InputMapper
        mapper = InputMapper(self.config_manager)
        key_events = mapper.parse_combo(combo_sequence_str, is_numpad=False)
        return self.execute_overlapping_combo(key_events)
