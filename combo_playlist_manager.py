import json
import os
import random
import time
import threading
from typing import List, Dict

from config_manager import ConfigManager
from game_monitor import GameMonitor
from combo_executor import ComboExecutor
from input_mapper import InputMapper

DEFAULT_PLAYLISTS = {
    "default": []
}

class ComboPlaylistManager:
    """
    Manages loading, saving, editing, and querying combo playlists from a JSON file.
    Includes a CLI menu interface for CRUD operations on playlists and combos.
    """
    def __init__(self, filepath: str = "playlists.json"):
        self.filepath = filepath
        self.first_run = False
        self.selected_playlist = "default"
        self.playlists = self.load_playlists()

    def load_playlists(self) -> dict:
        """
        Loads playlists from the JSON file. Creates defaults if it doesn't exist or is empty/corrupt.
        """
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            self.first_run = True
            self.save_playlists(DEFAULT_PLAYLISTS)
            return DEFAULT_PLAYLISTS.copy()
            
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.first_run = True
                    self.save_playlists(DEFAULT_PLAYLISTS)
                    return DEFAULT_PLAYLISTS.copy()
                playlists = json.loads(content)
                if not isinstance(playlists, dict) or not playlists:
                    self.first_run = True
                    self.save_playlists(DEFAULT_PLAYLISTS)
                    return DEFAULT_PLAYLISTS.copy()
                return playlists
        except Exception as e:
            print(f"[ComboPlaylistManager Warning] Error reading playlists: {e}. Resetting to default.")
            self.first_run = True
            self.save_playlists(DEFAULT_PLAYLISTS)
            return DEFAULT_PLAYLISTS.copy()

    def reload_playlists(self) -> None:
        """
        Reloads playlists from the JSON file to refresh the RAM cache.
        """
        self.playlists = self.load_playlists()

    def load_and_select_playlist(self, playlist_name: str) -> str:
        """
        Reloads playlists from the JSON file, checks if the selected playlist
        exists, and returns a safe fallback if it is missing.
        """
        self.reload_playlists()
        if playlist_name in self.playlists:
            self.selected_playlist = playlist_name
            return playlist_name
            
        names = self.get_playlist_names()
        if names:
            self.selected_playlist = names[0]
        else:
            self.selected_playlist = "default"
            if "default" not in self.playlists:
                self.playlists["default"] = []
                self.save_playlists()
        
        print(f"[ComboPlaylistManager Warning] Selected playlist '{playlist_name}' not found. Resetting to safe state: '{self.selected_playlist}'")
        return self.selected_playlist

    def save_playlists(self, playlists_data: dict = None) -> None:
        """
        Saves current playlists data to the JSON file.
        """
        if playlists_data is not None:
            self.playlists = playlists_data
            
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ComboPlaylistManager Error] Error writing playlists: {e}")

    def get_playlist_names(self) -> List[str]:
        """Returns list of loaded playlist names."""
        return list(self.playlists.keys())

    def get_playlist(self, name: str) -> List[str]:
        """Returns the combo list for a given playlist name."""
        return self.playlists.get(name, [])

    def pick_random_combo(self, name: str) -> str:
        """
        Picks a random combo string from the specified playlist.
        """
        combos = self.get_playlist(name)
        if not combos:
            return None
        return random.choice(combos)

    # ----------------------------------------------------
    # CRUD Operations
    # ----------------------------------------------------
    def create_playlist(self, name: str) -> None:
        """Creates a new empty playlist and auto-saves."""
        if name not in self.playlists:
            self.playlists[name] = []
            self.save_playlists()

    def delete_playlist(self, name: str) -> bool:
        """Deletes a playlist and auto-saves. Returns True if successful."""
        if name in self.playlists:
            self.playlists.pop(name)
            self.save_playlists()
            self.reload_playlists()
            return True
        return False

    def validate_combo_string(self, combo_str: str) -> bool:
        """
        Validates that a combo string can be successfully parsed.
        """
        if not combo_str.strip():
            return False
        try:
            from config_manager import ConfigManager
            from input_mapper import InputMapper
            cfg = ConfigManager()
            mapper = InputMapper(cfg)
            mapper.parse_combo(combo_str, is_numpad=True)
            return True
        except Exception:
            return False

    def add_combo(self, playlist_name: str, combo_sequence: str) -> bool:
        """
        Validates a combo string and appends it to a playlist, then auto-saves.
        """
        if not self.validate_combo_string(combo_sequence):
            print("[Validation Error] Combo contains invalid keys! Only directions 1-9, L, M, H, S, B, CL, GRAB, +, > and , are allowed.")
            return False
            
        if playlist_name not in self.playlists:
            self.playlists[playlist_name] = []
            
        self.playlists[playlist_name].append(combo_sequence.strip())
        self.save_playlists()
        return True

    def remove_combo(self, playlist_name: str, index: int) -> bool:
        """
        Removes a combo at the specified index and auto-saves.
        """
        if playlist_name in self.playlists:
            combos = self.playlists[playlist_name]
            if 0 <= index < len(combos):
                combos.pop(index)
                self.save_playlists()
                return True
        return False

    # ----------------------------------------------------
    # CRUD CLI Menus
    # ----------------------------------------------------
    def manage_playlists_cli(self) -> None:
        """
        Interactive CLI menu for managing playlists (creating, deleting, listings).
        """
        while True:
            print("\n" + "=" * 50)
            print("             PLAYLIST MANAGER MENU              ")
            print("=" * 50)
            print("  1. List Playlists")
            print("  2. Create New Playlist")
            print("  3. Delete Playlist")
            print("  4. Manage Combos in a Playlist")
            print("  5. Return to Main Menu")
            print("=" * 50)
            
            choice = input("Select an option (1-5): ").strip()
            
            if choice == '5':
                break
            elif choice == '1':
                print("\nPlaylists list:")
                for name in self.get_playlist_names():
                    print(f"  - {name}: {self.get_playlist(name)}")
            elif choice == '2':
                name = input("Enter new playlist name: ").strip()
                if not name:
                    print("Playlist name cannot be empty.")
                    continue
                if name in self.playlists:
                    print("Playlist already exists.")
                    continue
                self.create_playlist(name)
                print(f"Playlist '{name}' created successfully.")
            elif choice == '3':
                name = input("Enter playlist name to delete: ").strip()
                if name not in self.playlists:
                    print("Playlist does not exist.")
                    continue
                confirm = input(f"Are you sure you want to delete playlist '{name}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    if self.delete_playlist(name):
                        print(f"Playlist '{name}' deleted.")
            elif choice == '4':
                self.manage_combos_cli()
            else:
                print("Invalid choice.")

    def manage_combos_cli(self) -> None:
        """
        Interactive CLI menu for managing combos inside a chosen playlist (adding, removing, listings).
        """
        names = self.get_playlist_names()
        if not names:
            print("No playlists available. Please create one first.")
            return
            
        print("\nSelect a playlist to manage:")
        for idx, name in enumerate(names, 1):
            print(f"  {idx}. {name}")
            
        try:
            choice = input(f"Enter number (1-{len(names)}): ").strip()
            idx = int(choice) - 1
            if not (0 <= idx < len(names)):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
            
        selected_name = names[idx]
        
        while True:
            combos = self.get_playlist(selected_name)
            print("\n" + "=" * 50)
            print(f"         MANAGING PLAYLIST: {selected_name.upper()}         ")
            print("=" * 50)
            if not combos:
                print("  (No combos in this playlist)")
            else:
                for c_idx, combo in enumerate(combos, 1):
                    print(f"  {c_idx}. {combo}")
            print("-" * 50)
            print("  1. Add Combo to Playlist")
            print("  2. Remove Combo from Playlist")
            print("  3. Back to Playlist Menu")
            print("=" * 50)
            
            choice = input("Select an option (1-3): ").strip()
            
            if choice == '3':
                break
            elif choice == '1':
                print("\nRules: Combos must only contain directions 1-9, actions L, M, H, S, B, CL.")
                print("Examples: '236H', '6+H', '236CL, 2B'")
                new_combo = input("Enter combo string: ").strip()
                if self.add_combo(selected_name, new_combo):
                    print(f"Combo '{new_combo}' added successfully.")
            elif choice == '2':
                if not combos:
                    print("Playlist is already empty.")
                    continue
                try:
                    c_choice = input(f"Enter combo index to remove (1-{len(combos)}): ").strip()
                    c_idx = int(c_choice) - 1
                    if 0 <= c_idx < len(combos):
                        removed = combos[c_idx]
                        if self.remove_combo(selected_name, c_idx):
                            print(f"Removed combo '{removed}'.")
                    else:
                        print("Invalid index.")
                except ValueError:
                    print("Invalid input.")
            else:
                print("Invalid choice.")


class PlaylistOrchestrator:
    """
    Manages the background loop of executing random combos from a selected playlist.
    Uses hotkeys (Start/Stop) to run/pause execution and monitors GameMonitor for safety.
    """
    def __init__(
        self,
        playlist_name: str,
        playlist_manager: ComboPlaylistManager,
        executor: ComboExecutor,
        mapper: InputMapper,
        game_monitor: GameMonitor,
        fps: float = 60.0
    ):
        self.playlist_name = playlist_name
        self.playlist_manager = playlist_manager
        self.executor = executor
        self.mapper = mapper
        self.game_monitor = game_monitor
        self.fps = fps
        
        self._stop_event = threading.Event()
        self._thread = None

    @property
    def playlists(self):
        return self.playlist_manager.playlists

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """Starts the playlist loop in a background thread."""
        if self._thread and self._thread.is_alive():
            print("[Playlist Orchestrator] Already running.")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self.run_playlist,
            args=(self.playlist_name, self._stop_event),
            daemon=True
        )
        self._thread.start()
        print(f"[Playlist Orchestrator] Playlist loop activated for '{self.playlist_name}'.")

    def stop(self):
        """Stops the playlist loop and releases all keys."""
        if self._stop_event.is_set():
            return
            
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self.executor.reset_executor_state()
        print("[Playlist Orchestrator] Playlist loop deactivated.")

    def run_playlist(self, playlist_name: str, stop_event: threading.Event) -> None:
        """
        Main playlist loop running inside the background thread.
        Picks random combos, parses them, and executes them with a 60-120 frames random delay.
        """
        print(f"[Playlist Orchestrator Thread] active loop started for playlist: '{playlist_name}'")
        
        while not stop_event.is_set():
            # Ensure the playlist still exists in memory (not deleted)
            if playlist_name not in self.playlists:
                print(f"[Playlist Orchestrator Error] Playlist '{playlist_name}' was deleted or does not exist. Aborting loop.")
                break

            # 1. Always check GameMonitor.is_game_running() and is_game_focused() before starting any new combo
            if not self.game_monitor.is_game_running() or not self.game_monitor.is_game_focused():
                # Release keys and wait if game is not active/focused
                self.executor.reset_executor_state()
                time.sleep(0.5)
                continue
                
            # 2. Pick a random combo from the playlist
            combo_str = self.playlist_manager.pick_random_combo(playlist_name)
            if not combo_str:
                print(f"[Playlist Orchestrator Error] Playlist '{playlist_name}' is empty. Pausing loop.")
                time.sleep(1.0)
                continue
                
            print(f"\n[Playlist Orchestrator] Selected random combo: '{combo_str}'")
            
            # 3. Parse combo to timed overlapping key events
            try:
                is_numpad = any(char.isdigit() for char in combo_str)
                key_events = self.mapper.parse_combo(combo_str, is_numpad=is_numpad)
                if not key_events:
                    print(f"[Playlist Orchestrator Error] Failed to generate key events for combo '{combo_str}'. Skipping.")
                    time.sleep(1.0)
                    continue
            except Exception as e:
                print(f"[Playlist Orchestrator Error] Failed to parse combo '{combo_str}': {e}. Skipping.")
                time.sleep(1.0)
                continue
                
            # 4. Execute the combo
            # Runs synchronously inside this background thread
            success = self.executor.execute_overlapping_combo(key_events)
            if not success:
                print("[Playlist Orchestrator] Combo execution aborted or failed.")
                
            # 5. Add random delay (60-120 frames) before next combo selection
            if not stop_event.is_set():
                delay_frames = random.randint(60, 120)
                delay_sec = delay_frames / self.fps
                print(f"[Playlist Orchestrator] Waiting {delay_frames} frames ({delay_sec:.3f}s)...")
                
                # Precise wait with fail-safe checks during sleep
                start_sleep = time.perf_counter()
                while time.perf_counter() - start_sleep < delay_sec:
                    if stop_event.is_set():
                        break
                    # Poll game monitor for fail-safe
                    if not self.game_monitor.is_game_running() or not self.game_monitor.is_game_focused():
                        self.executor.reset_executor_state()
                        break
                    time.sleep(0.05)
                    
        self.executor.reset_executor_state()
        print(f"[Playlist Orchestrator Thread] Loop finished for: '{playlist_name}'")
