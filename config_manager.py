import json
import os
from direct_input import SCAN_CODES

DEFAULT_CONFIG = {
    "bindings": {
        "Up": "w",
        "Down": "s",
        "Left": "a",
        "Right": "d",
        "Light": "j",
        "Medium": "k",
        "Heavy": "l",
        "Special": "i",
        "Burst": "u",
        "Collab": "o"
    },
    "is_player2_right": True,
    "game_process": "",
    "game_window": ""
}

class ConfigManager:
    """
    Manages reading and writing action-to-key configuration bindings in JSON format.
    Provides methods to modify bindings through an interactive CLI.
    """
    def __init__(self, filepath: str = "config.json"):
        self.filepath = filepath
        self.config = self.load_config()

    def load_config(self) -> dict:
        """
        Loads configuration from the JSON file. If it doesn't exist,
        initializes with default bindings. Removes obsolete 'Attack' bindings.
        """
        if not os.path.exists(self.filepath):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        
        try:
            config_changed = False
            with open(self.filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Ensure bindings dictionary exists
                if "bindings" not in config:
                    config["bindings"] = DEFAULT_CONFIG["bindings"].copy()
                    config_changed = True
                
                # Merge default keys if missing
                for action, key in DEFAULT_CONFIG["bindings"].items():
                    if action not in config["bindings"]:
                        config["bindings"][action] = key
                        config_changed = True
                
                # Clean up legacy 'Attack' key if it exists
                if "Attack" in config["bindings"]:
                    config["bindings"].pop("Attack")
                    config_changed = True
                    
                # Ensure is_player2_right setting exists
                if "is_player2_right" not in config:
                    config["is_player2_right"] = DEFAULT_CONFIG["is_player2_right"]
                    config_changed = True
                    
                # Ensure process and window settings exist
                if "game_process" not in config:
                    config["game_process"] = DEFAULT_CONFIG["game_process"]
                    config_changed = True
                if "game_window" not in config:
                    config["game_window"] = DEFAULT_CONFIG["game_window"]
                    config_changed = True
                
                # If we modified/cleaned anything, save back to file
                if config_changed:
                    self.save_config(config)
                    
                return config
        except Exception as e:
            print(f"[ConfigManager Warning] Error reading config: {e}. Using defaults.")
            return DEFAULT_CONFIG.copy()

    def save_config(self, config_data: dict = None) -> None:
        """
        Saves the current configuration data to the JSON file.
        """
        if config_data is not None:
            self.config = config_data
            
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager Error] Error writing config: {e}")

    def get_bindings(self) -> dict:
        """Returns the dictionary of active key bindings."""
        return self.config.get("bindings", {})

    def get_key_for_action(self, action: str) -> str:
        """
        Retrieves the key name mapped to a given action (case-insensitive search).
        """
        action_clean = action.strip()
        bindings = self.get_bindings()
        for act, key in bindings.items():
            if act.lower() == action_clean.lower():
                return key
        return None

    def update_binding(self, action: str, key_name: str) -> bool:
        """
        Updates a single action-to-key binding after validating the key exists in SCAN_CODES.
        """
        key_clean = key_name.lower().strip()
        if key_clean not in SCAN_CODES:
            print(f"[ConfigManager Error] Key '{key_name}' is not supported in SCAN_CODES.")
            return False
            
        bindings = self.config["bindings"]
        matched_action = None
        for act in bindings.keys():
            if act.lower() == action.lower().strip():
                matched_action = act
                break
                
        if matched_action:
            bindings[matched_action] = key_clean
        else:
            bindings[action.strip()] = key_clean
            
        self.save_config()
        return True

    def configure_bindings_cli(self) -> None:
        """
        An interactive CLI menu to view, add, or edit key bindings.
        """
        while True:
            print("\n" + "=" * 50)
            print("         PLAYER 2 KEY BINDINGS CONFIGURATION        ")
            print("=" * 50)
            bindings = self.get_bindings()
            for i, (action, key) in enumerate(bindings.items(), 1):
                print(f"  {i}. {action:15} -> {key.upper()}")
            print("-" * 50)
            print(f"  P. Game Process    -> {self.config.get('game_process')}")
            print(f"  W. Game Window     -> {self.config.get('game_window')}")
            p2_side = "RIGHT (Facing Left)" if self.config.get("is_player2_right", True) else "LEFT (Facing Right)"
            print(f"  S. Player 2 Side   -> {p2_side}")
            print("-" * 50)
            print("  A. Add new action mapping")
            print("  Q. Save and Return to Main Menu")
            print("=" * 50)
            
            choice = input("Select an option to edit (1-N, A, P, W, S, Q): ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice == 'A':
                new_action = input("Enter new action name (e.g. 'Jump'): ").strip()
                if not new_action:
                    print("Action name cannot be empty.")
                    continue
                new_key = input(f"Enter key for '{new_action}' (e.g. 'space', 'u'): ").strip().lower()
                if self.update_binding(new_action, new_key):
                    print(f"[ConfigManager] Successfully mapped '{new_action}' to '{new_key.upper()}'.")
            elif choice == 'P':
                new_proc = input("Enter game process name (e.g., 'Idol Showdown.exe'): ").strip()
                if new_proc:
                    self.config["game_process"] = new_proc
                    self.save_config()
                    print(f"Game process updated to: {new_proc}")
            elif choice == 'W':
                new_win = input("Enter game window title match (e.g., 'Idol Showdown'): ").strip()
                if new_win:
                    self.config["game_window"] = new_win
                    self.save_config()
                    print(f"Game window title match updated to: {new_win}")
            elif choice == 'S':
                self.config["is_player2_right"] = not self.config.get("is_player2_right", True)
                self.save_config()
                new_side = "RIGHT (Facing Left)" if self.config.get("is_player2_right", True) else "LEFT (Facing Right)"
                print(f"Player 2 side updated to: {new_side}")
            else:
                try:
                    idx = int(choice) - 1
                    actions_list = list(bindings.keys())
                    if 0 <= idx < len(actions_list):
                        action_to_edit = actions_list[idx]
                        current_key = bindings[action_to_edit]
                        print(f"Editing '{action_to_edit}' (current key: '{current_key.upper()}')")
                        print("Supported keys include letters (a-z), numbers (0-9), arrow keys (up, down, left, right),")
                        print("numpad keys (num_1 to num_9, num_0), space, enter, shift, ctrl, alt, etc.")
                        new_key = input(f"Enter new key for '{action_to_edit}': ").strip().lower()
                        if new_key:
                            if self.update_binding(action_to_edit, new_key):
                                print(f"[ConfigManager] Updated '{action_to_edit}' -> '{new_key.upper()}'.")
                        else:
                            print("Cancelled.")
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Invalid choice. Please enter a valid number or menu letter.")
