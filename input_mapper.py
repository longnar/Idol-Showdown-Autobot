import re
import random
from typing import List, Dict
from config_manager import ConfigManager

class InputMapper:
    """
    Translates fighting game 'Numpad Notation' combinations (e.g. '236H', '623L', '6+H')
    or action name combos into a time-based overlapping hold format.
    
    Supports Player 2 direction flipping based on the 'is_player2_right' configuration setting.
    
    Numpad Layout for Directions (Standard Player 1 / Facing Right):
      7 (Up-Back)    8 (Up)      9 (Up-Forward)
      4 (Back)       5 (Neutral) 6 (Forward)
      1 (Down-Back)  2 (Down)    3 (Down-Forward)
      
    Action Notations:
      L  -> Light (Attack)
      M  -> Medium (Attack)
      H  -> Heavy (Attack)
      S  -> Special (Attack)
      B  -> Burst
      CL -> Collab
    """
    # Standard P1 direction mapping
    NUMPAD_DIRECTIONS = {
        '1': ['Down', 'Left'],
        '2': ['Down'],
        '3': ['Down', 'Right'],
        '4': ['Left'],
        '5': [],  # Neutral (no keys pressed)
        '6': ['Right'],
        '7': ['Up', 'Left'],
        '8': ['Up'],
        '9': ['Up', 'Right']
    }
    
    # Attack and special action maps
    ACTION_MAP = {
        'L': 'Light',
        'M': 'Medium',
        'H': 'Heavy',
        'S': 'Special',
        'B': 'Burst',
        'CL': 'Collab'
    }

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the InputMapper with a ConfigManager instance to resolve actions to physical keys.
        
        :param config_manager: ConfigManager instance.
        """
        self.config_manager = config_manager

    def tokenize(self, combo_string: str) -> List[str]:
        """
        Tokenizes a single continuous block of numpad notation into a list of steps.
        E.g., "236H"      -> ["2", "3", "6", "H"]
        E.g., "236Cl"     -> ["2", "3", "6", "CL"]
        E.g., "6+H"       -> ["6+H"]
        E.g., "236+H"     -> ["2", "3", "6+H"]
        """
        # Clean the string: remove spaces and convert to uppercase
        clean_str = combo_string.replace(" ", "").upper()
        
        steps = []
        i = 0
        n = len(clean_str)
        
        while i < n:
            char = clean_str[i]
            
            # Check for CL (Collab)
            if char == 'C' and i + 1 < n and clean_str[i+1] == 'L':
                token = "CL"
                i += 2
            else:
                token = char
                i += 1
                
            # Check if next character is a '+' operator. If so, build a compound step.
            if i < n and clean_str[i] == '+':
                i += 1  # Skip '+'
                if i < n:
                    if clean_str[i] == 'C' and i + 1 < n and clean_str[i+1] == 'L':
                        next_token = "CL"
                        i += 2
                    else:
                        next_token = clean_str[i]
                        i += 1
                    token = f"{token}+{next_token}"
            steps.append(token)
            
        return steps

    def _split_combo_by_operators(self, combo_string: str):
        """
        Splits a combo string by operators ',' and '>' in chronological order,
        returning a list of combo blocks and a list of connection operators.
        
        E.g., "236H > 623L, 5L" -> (["236H", "623L", "5L"], [">", ","])
        """
        tokens = re.split(r'([,>])', combo_string)
        blocks = []
        operators = []
        
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            if t in (',', '>'):
                operators.append(t)
            else:
                blocks.append(t)
                
        return blocks, operators

    def parse_action_combo_to_time_based(self, combo_string: str) -> List[Dict]:
        """
        Parses an action name combo (comma or > separated, e.g., 'Down > Forward > Light, Attack')
        into a list of structured time-based key events.
        
        :param combo_string: The combo sequence string of action names.
        :return: List of key event dictionaries.
        """
        blocks, operators = self._split_combo_by_operators(combo_string)
        key_events = []
        
        current_time = 0.0
        delay_frames = self.config_manager.config.get("delay_frames", 30)
        
        for idx, block in enumerate(blocks):
            sub_actions = [sa.strip() for sa in block.split('+')]
            keys_for_step = []
            for action in sub_actions:
                key = self.config_manager.get_key_for_action(action)
                if key:
                    keys_for_step.append(key)
                    
            if not keys_for_step:
                continue
                
            # Standard 5 frames hold for action name steps
            hold_duration = 5.0 / 60.0 
            
            for key in keys_for_step:
                key_events.append({
                    "key": key,
                    "start_time": current_time,
                    "hold_duration": hold_duration
                })
                
            # If not the last block, calculate next block start time based on operator
            if idx < len(blocks) - 1:
                op = operators[idx] if idx < len(operators) else ","
                if op == '>':
                    # Immediate chain: 5 frames transition
                    current_time += hold_duration + (5.0 / 60.0)
                else:
                    # Comma: delay_frames transition
                    current_time += hold_duration + (delay_frames / 60.0)
                
        return key_events

    def parse_numpad_combo_to_time_based(self, combo_string: str) -> List[Dict]:
        """
        Parses a numpad notation combo (e.g. '236H > 623L, 5L')
        into a list of structured time-based key events with overlapping holds.
        
        :param combo_string: The combo sequence string in Numpad Notation.
        :return: List of key event dictionaries.
        """
        is_p2_right = self.config_manager.config.get("is_player2_right", True)
        
        # Build direction mapping based on facing side
        if is_p2_right:
            direction_map = {
                '1': ['Down', 'Right'],
                '2': ['Down'],
                '3': ['Down', 'Left'],
                '4': ['Right'],
                '5': [],
                '6': ['Left'],
                '7': ['Up', 'Right'],
                '8': ['Up'],
                '9': ['Up', 'Left']
            }
        else:
            direction_map = self.NUMPAD_DIRECTIONS

        blocks, operators = self._split_combo_by_operators(combo_string)
        key_events = []
        
        current_block_start_time = 0.0
        delay_frames = self.config_manager.config.get("delay_frames", 30)
        
        for b_idx, block in enumerate(blocks):
            tokens = self.tokenize(block)
            num_tokens = len(tokens)
            if num_tokens == 0:
                continue
                
            # Step 1: Assign start frame for each token in the block
            token_start_frames = []
            current_frame = 0
            for t_idx in range(num_tokens):
                token_start_frames.append(current_frame)
                current_frame += 3  # 3 frames step interval for motion input
                
            # Step 2: Build a map of key presence across tokens
            key_presence = {}
            token_keys_list = []
            token_is_attack = []
            
            for token in tokens:
                sub_tokens = token.split('+')
                step_actions = []
                is_attack = False
                
                for t in sub_tokens:
                    t = t.strip()
                    if not t:
                        continue
                    if t in direction_map:
                        step_actions.extend(direction_map[t])
                    elif t in self.ACTION_MAP:
                        step_actions.append(self.ACTION_MAP[t])
                        is_attack = True
                
                # Resolve actions to physical keys
                keys = []
                for act in step_actions:
                    k = self.config_manager.get_key_for_action(act)
                    if k:
                        keys.append(k)
                        
                token_keys_list.append(set(keys))
                token_is_attack.append(is_attack)
                
                for k in keys:
                    if k not in key_presence:
                        key_presence[k] = [False] * num_tokens
                        
            # Fill key presence map
            for t_idx, keys_set in enumerate(token_keys_list):
                for k in keys_set:
                    key_presence[k][t_idx] = True
                    
            # Step 3: Find continuous runs for each key in this block
            block_max_end_time = 0.0
            
            for key, presence in key_presence.items():
                in_run = False
                run_start_token = 0
                
                for t_idx in range(num_tokens):
                    if presence[t_idx]:
                        if not in_run:
                            in_run = True
                            run_start_token = t_idx
                    else:
                        if in_run:
                            in_run = False
                            run_start_frame = token_start_frames[run_start_token]
                            run_end_frame = token_start_frames[t_idx] + 1
                            run_duration = run_end_frame - run_start_frame
                            
                            start_time = current_block_start_time + (run_start_frame / 60.0)
                            hold_duration = run_duration / 60.0
                            
                            key_events.append({
                                "key": key,
                                "start_time": start_time,
                                "hold_duration": hold_duration
                            })
                            block_max_end_time = max(block_max_end_time, start_time + hold_duration)
                            
                if in_run:
                    run_start_frame = token_start_frames[run_start_token]
                    final_hold_frames = 5 if token_is_attack[-1] else 3
                    run_end_frame = token_start_frames[-1] + final_hold_frames
                    run_duration = run_end_frame - run_start_frame
                    
                    start_time = current_block_start_time + (run_start_frame / 60.0)
                    hold_duration = run_duration / 60.0
                    
                    key_events.append({
                        "key": key,
                        "start_time": start_time,
                        "hold_duration": hold_duration
                    })
                    block_max_end_time = max(block_max_end_time, start_time + hold_duration)
                    
            # If not the last block, set start time of next block
            if b_idx < len(blocks) - 1:
                op = operators[b_idx] if b_idx < len(operators) else ","
                if op == '>':
                    # Immediate chain: 5 frames delay
                    current_block_start_time = block_max_end_time + (5.0 / 60.0)
                else:
                    # Comma: delay_frames delay
                    current_block_start_time = block_max_end_time + (delay_frames / 60.0)
                    
        # Sort key events by start time
        key_events.sort(key=lambda x: x["start_time"])
        return key_events

    def parse_combo(self, combo_string: str, is_numpad: bool = True) -> List[Dict]:
        """
        Parses a combo string into a list of structured time-based key events.
        
        :param combo_string: The combo sequence string.
        :param is_numpad: True if Numpad Notation, False if Action Names.
        :return: List of key event dictionaries.
        """
        if is_numpad:
            return self.parse_numpad_combo_to_time_based(combo_string)
        else:
            return self.parse_action_combo_to_time_based(combo_string)
