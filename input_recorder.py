import time
import threading
import keyboard
from typing import List, Dict

class InputRecorder:
    """
    Globally hooks keyboard events and translates raw inputs into standard fighting game Numpad Notation.
    Filters out system repeats and non-configured keys based on the user's config bindings.
    """
    def __init__(self):
        self.is_recording = False
        self.recorded_events = []
        self.start_time = 0.0
        self._hooked = False
        self.live_combo_string = ""
        
        # Track currently held physical keys to filter OS key-repeat events
        self._held_keys = set()
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self.recorded_events = []
            self._held_keys.clear()
            self.start_time = time.time()
            self.is_recording = True
            self.live_combo_string = ""
            if not self._hooked:
                keyboard.hook(self._on_key_event)
                self._hooked = True

    def stop(self) -> str:
        with self._lock:
            if self._hooked:
                keyboard.unhook(self._on_key_event)
                self._hooked = False
            self.is_recording = False
            # Final processing
            combo = self.process_to_numpad_notation()
            self.live_combo_string = combo
            return combo

    def reset(self):
        with self._lock:
            self.recorded_events = []
            self._held_keys.clear()
            self.start_time = time.time()
            self.live_combo_string = ""

    def _on_key_event(self, event):
        if not self.is_recording:
            return
            
        key_name = event.name.lower()
        event_type = event.event_type # 'down' or 'up'
        
        with self._lock:
            # Filter auto-repeat 'down' events
            if event_type == 'down':
                if key_name in self._held_keys:
                    return # Ignore repeat
                self._held_keys.add(key_name)
            elif event_type == 'up':
                if key_name in self._held_keys:
                    self._held_keys.remove(key_name)
                else:
                    return # Ignore key up for untracked keys
            
            rel_time_ms = int((event.time - self.start_time) * 1000)
            self.recorded_events.append({
                "key": key_name,
                "type": event_type,
                "timestamp": rel_time_ms
            })
            
            # Update the live string periodically
            try:
                self.live_combo_string = self.process_to_numpad_notation()
            except Exception:
                pass

    def process_to_numpad_notation(self) -> str:
        """
        Processes raw recorded events and returns a structured Numpad Notation combo string.
        """
        if not self.recorded_events:
            return ""
            
        # Get latest configuration
        from config_manager import ConfigManager
        config_mgr = ConfigManager()
        bindings = config_mgr.config.get("bindings", {})
        
        # Build reverse mapping: key_name (lower) -> action_name
        key_to_action = {}
        for action, key in bindings.items():
            if key:
                key_to_action[key.lower()] = action
                
        # Common key aliases (e.g. arrow keys)
        arrow_aliases = {
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right"
        }
        for alias, action in arrow_aliases.items():
            if action in bindings:
                key_to_action[alias] = action

        # 1. Reconstruct key held states chronologically
        states = [] # list of (timestamp, set_of_held_actions)
        current_actions = set()
        
        # Sort events by timestamp
        sorted_events = sorted(self.recorded_events, key=lambda x: x["timestamp"])
        
        for ev in sorted_events:
            key = ev["key"]
            action = key_to_action.get(key)
            if not action:
                continue
                
            if ev["type"] == "down":
                current_actions.add(action)
            elif ev["type"] == "up":
                if action in current_actions:
                    current_actions.remove(action)
            
            # Record state at this timestamp
            states.append((ev["timestamp"], set(current_actions)))
            
        if not states:
            return ""

        # Helper to map directions to numpad digit
        def get_numpad_direction(active_dirs) -> str:
            is_up = "Up" in active_dirs
            is_down = "Down" in active_dirs
            is_left = "Left" in active_dirs
            is_right = "Right" in active_dirs
            
            if is_up and is_down:
                is_up = is_down = False
            if is_left and is_right:
                is_left = is_right = False
                
            if is_up and is_left: return "7"
            if is_up and is_right: return "9"
            if is_up: return "8"
            if is_down and is_left: return "1"
            if is_down and is_right: return "3"
            if is_down: return "2"
            if is_left: return "4"
            if is_right: return "6"
            return "5"

        ATTACK_SYMBOLS = {
            "Light": "L",
            "Medium": "M",
            "Heavy": "H",
            "Special": "S",
            "Burst": "B",
            "Collab": "CL",
            "Grab": "GRAB"
        }

        # 2. Extract discrete combo blocks
        blocks = []
        current_block = None
        
        for timestamp, active_actions in states:
            dirs = {a for a in active_actions if a in ("Up", "Down", "Left", "Right")}
            attacks = {a for a in active_actions if a in ATTACK_SYMBOLS}
            
            dir_digit = get_numpad_direction(dirs)
            
            if not dirs and not attacks:
                # Neutral state (all keys released). If block has attacks, close it.
                if current_block and current_block["attacks"]:
                    blocks.append(current_block)
                    current_block = None
                continue
                
            if not current_block:
                current_block = {
                    "start_time": timestamp,
                    "end_time": timestamp,
                    "directions": [],
                    "attacks": set()
                }
                
            current_block["end_time"] = timestamp
            
            if dir_digit != "5":
                if not current_block["directions"] or current_block["directions"][-1] != dir_digit:
                    current_block["directions"].append(dir_digit)
                    
            if attacks:
                att_symbols = {ATTACK_SYMBOLS[att] for att in attacks}
                # Check if a new attack key has been pressed
                new_attacks = att_symbols - current_block["attacks"]
                if new_attacks and current_block["attacks"]:
                    # Close current and start a new block
                    blocks.append(current_block)
                    current_block = {
                        "start_time": timestamp,
                        "end_time": timestamp,
                        "directions": [],
                        "attacks": set()
                    }
                    if dir_digit != "5":
                        current_block["directions"].append(dir_digit)
                    current_block["attacks"] = att_symbols
                else:
                    current_block["attacks"].update(att_symbols)
                    
        if current_block:
            blocks.append(current_block)

        # 3. Format blocks and connect them with chronological operators (> or ,)
        formatted_blocks = []
        for b in blocks:
            dir_str = "".join(b["directions"])
            att_list = sorted(list(b["attacks"]))
            
            if not dir_str and att_list:
                dir_str = "5"
                
            if dir_str and not att_list:
                block_str = dir_str
            elif dir_str and att_list:
                att_str = "+".join(att_list)
                if len(dir_str) > 1 and len(att_list) == 1:
                    block_str = f"{dir_str}{att_str}"
                else:
                    if len(att_list) > 1:
                        block_str = f"{dir_str}+{att_str}"
                    else:
                        block_str = f"{dir_str}{att_str}"
            else:
                continue
                
            formatted_blocks.append((b["start_time"], b["end_time"], block_str))

        if not formatted_blocks:
            return ""
            
        result_str = formatted_blocks[0][2]
        for i in range(1, len(formatted_blocks)):
            prev_end = formatted_blocks[i-1][1]
            curr_start = formatted_blocks[i][0]
            gap = curr_start - prev_end
            
            if gap < 400:
                result_str += " > " + formatted_blocks[i][2]
            else:
                result_str += " , " + formatted_blocks[i][2]
                
        return result_str
