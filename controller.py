import ctypes
import time
import random
import threading
from typing import List, Tuple
from sequence import InputSequence
from direct_input import press_key, release_key, SCAN_CODES
from game_monitor import GameMonitor

class FightingGameController:
    """Manages the input loop, timing, active window checking, and execution of sequences."""
    def __init__(
        self,
        sequences: List[InputSequence],
        window_title: str,
        fps: float = 60.0,
        delay_range_frames: Tuple[int, int] = (30, 60),
        random_mode: bool = True,
        game_monitor: GameMonitor = None
    ):
        self.sequences = sequences
        self.window_title = window_title.lower()
        self.fps = fps
        self.delay_range_frames = delay_range_frames
        self.random_mode = random_mode
        self.game_monitor = game_monitor
        
        self._running_event = threading.Event()
        self._thread = None
        self._current_sequence_index = 0
        
        # Optimize Windows scheduler timing resolution
        try:
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception as e:
            print(f"[Warning] Failed to set Windows timer resolution: {e}")

    def get_active_window_title(self) -> str:
        """Retrieves the title of the active foreground window using Windows ctypes API."""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def is_game_focused(self) -> bool:
        """Checks if the target window is currently focused."""
        active_title = self.get_active_window_title().lower()
        # Returns True if target window title is a substring of the active window title
        return self.window_title in active_title

    def precise_sleep(self, duration_sec: float):
        """High-resolution sleep to achieve low latency and precise frame timings."""
        start_time = time.perf_counter()
        
        # Sleep for the bulk of the duration to free up CPU
        if duration_sec > 0.002:
            time.sleep(duration_sec - 0.001)
            
        # Busy-wait for the remaining sub-millisecond portion
        while time.perf_counter() - start_time < duration_sec:
            if not self._running_event.is_set():
                break

    def release_all_keys(self):
        """Safety function to release all defined keys to prevent keys getting stuck."""
        for key in SCAN_CODES.keys():
            release_key(key)

    def execute_sequence(self, sequence: InputSequence):
        """Executes a single InputSequence step-by-step."""
        print(f"[Bot] Executing sequence: {sequence.name}")
        for step in sequence.steps:
            if not self._running_event.is_set():
                break
                
            # Fail-safe check
            if self.game_monitor and not self.game_monitor.check_fail_safe():
                print("[Bot Warning] Fail-safe triggered: Game lost focus or is not running! Aborting sequence.")
                break
                
            # Press all keys in the step
            for key in step.keys:
                press_key(key)
                
            # Hold the keys for the specified duration
            duration_sec = step.duration_frames / self.fps
            self.precise_sleep(duration_sec)
            
            # Release all keys in the step
            for key in step.keys:
                release_key(key)
                
        # Final safety cleanup after sequence completes
        self.release_all_keys()

    def _loop(self):
        """Main execution loop run inside the background thread."""
        print("[Bot] Input loop started.")
        while self._running_event.is_set():
            # Check if game is running and focused using GameMonitor if available
            if self.game_monitor:
                if not self.game_monitor.check_fail_safe():
                    # Game is not focused or not running, release keys and wait
                    self.release_all_keys()
                    time.sleep(0.5)
                    continue
            else:
                # Fallback to simple focus check
                if not self.is_game_focused():
                    self.release_all_keys()
                    time.sleep(0.5)
                    continue
                
            # Choose the next sequence
            if not self.sequences:
                print("[Bot] No sequences configured. Stopping.")
                break
                
            if self.random_mode:
                sequence = random.choice(self.sequences)
            else:
                sequence = self.sequences[self._current_sequence_index]
                self._current_sequence_index = (self._current_sequence_index + 1) % len(self.sequences)
                
            # Execute the chosen sequence
            self.execute_sequence(sequence)
            
            # Calculate and execute random delay between sequences
            min_frames, max_frames = self.delay_range_frames
            delay_frames = random.randint(min_frames, max_frames)
            delay_sec = delay_frames / self.fps
            
            print(f"[Bot] Waiting for {delay_frames} frames ({delay_sec:.3f}s)...")
            self.precise_sleep(delay_sec)
            
        self.release_all_keys()
        print("[Bot] Input loop stopped.")

    def start(self):
        """Starts the automation loop in a background thread."""
        if self._running_event.is_set():
            print("[Bot] Already running.")
            return
            
        self._running_event.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Bot] Automation loop activated.")

    def stop(self):
        """Stops the automation loop and releases all keys."""
        if not self._running_event.is_set():
            print("[Bot] Already stopped.")
            return
            
        self._running_event.clear()
        if self._thread:
            self._thread.join(timeout=2.0)
        self.release_all_keys()
        print("[Bot] Automation loop deactivated.")

    def __del__(self):
        # Restore Windows timer resolution when object is destroyed
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass
