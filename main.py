import sys
import time
import config
from controller import FightingGameController
from hotkey import WindowsHotkeyListener
from config_manager import ConfigManager
from game_monitor import GameMonitor
from combo_executor import ComboExecutor
from input_mapper import InputMapper
from combo_playlist_manager import ComboPlaylistManager, PlaylistOrchestrator

def run_bot_mode(config_manager: ConfigManager, game_monitor: GameMonitor):
    # Fetch window title from ConfigManager
    window_title = config_manager.config.get("game_window", config.TARGET_GAME_WINDOW)
    process_name = config_manager.config.get("game_process", "")
    
    start_hk = config_manager.config.get("start_hotkey", "f9").lower()
    stop_hk = config_manager.config.get("stop_hotkey", "f10").lower()
    
    print("\n" + "=" * 60)
    print("                      RUNNING AUTO BOT MODE                     ")
    print("=" * 60)
    print(f"Target Window:  '{window_title}'")
    print(f"Game Process:   '{process_name}'")
    print(f"Frame Rate:     {config.FPS} FPS")
    print(f"Start Hotkey:   {start_hk.upper()}")
    print(f"Stop Hotkey:    {stop_hk.upper()}")
    print(f"Random Mode:    {config.RANDOM_MODE}")
    print("-" * 60)
    
    controller = FightingGameController(
        sequences=config.SEQUENCES,
        window_title=window_title,
        fps=config.FPS,
        delay_range_frames=(config.DELAY_MIN_FRAMES, config.DELAY_MAX_FRAMES),
        random_mode=config.RANDOM_MODE,
        game_monitor=game_monitor
    )
    
    listener = WindowsHotkeyListener()
    try:
        listener.register_hotkey(start_hk, controller.start)
        listener.register_hotkey(stop_hk, controller.stop)
    except ValueError as e:
        print(f"[Error] {e}")
        return
        
    listener.start()
    
    print("Bot service is active and listening for hotkeys...")
    print(f"Press {start_hk.upper()} to start execution loop, {stop_hk.upper()} to pause.")
    print("Press ENTER in this console to stop the service and return to main menu.")
    print("-" * 60)
    
    try:
        # Wait for the user to press Enter to stop the bot
        input()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        controller.stop()
        print("[Bot] Bot service stopped. Returned all virtual key states.")

def execute_custom_combo_mode(config_manager: ConfigManager, game_monitor: GameMonitor):
    window_title = config_manager.config.get("game_window", config.TARGET_GAME_WINDOW)
    process_name = config_manager.config.get("game_process", "")
    
    print("\n" + "=" * 60)
    print("                    EXECUTE CUSTOM COMBO MODE                   ")
    print("=" * 60)
    print("Choose Combo Input Format:")
    print("  1. Action Names (e.g., 'Down, Forward, Attack' or 'Down+Right, Attack')")
    print("  2. Numpad Notation (e.g., '236H', '623L', '6+H', '236CL')")
    print("-" * 60)
    
    fmt_choice = input("Select format (1 or 2): ").strip()
    if fmt_choice not in ('1', '2'):
        print("Invalid choice. Returning to menu.")
        return
        
    print("-" * 60)
    if fmt_choice == '1':
        print("Instructions:")
        print("  - Input actions separated by commas. Combine simultaneous presses with '+'")
        print(f"  - Key bindings: {config_manager.get_bindings()}")
        combo_str = input("\nEnter combo sequence: ").strip()
    else:
        print("Instructions:")
        print("  - Input directions (1-9) followed by action letters (L, M, H, S, B, CL)")
        print("  - Combine simultaneous presses with '+'")
        print("  - Directions: 7=UpBack, 8=Up, 9=UpForward, 4=Back, 6=Forward, 1=DownBack, 2=Down, 3=DownForward")
        print("  - Actions: L=Light, M=Medium, H=Heavy, S=Special, B=Burst, CL=Collab")
        print(f"  - Key bindings: {config_manager.get_bindings()}")
        combo_str = input("\nEnter numpad combo (e.g. '236H'): ").strip()
        
    if not combo_str:
        print("Empty combo. Returning to menu.")
        return
        
    # Check if game is running first
    if not game_monitor.is_game_running():
        print(f"[Warning] Target process '{process_name}' is not running!")
        print("Please start the game before running the combo.")
        input("\nPress Enter to return...")
        return
        
    executor = ComboExecutor(
        config_manager=config_manager,
        game_monitor=game_monitor,
        fps=config.FPS
    )
    
    mapper = InputMapper(config_manager)
    try:
        is_numpad = (fmt_choice == '2')
        key_events = mapper.parse_combo(combo_str, is_numpad=is_numpad)
        if not key_events:
            print("[ComboExecutor Error] No key events could be generated.")
            input("\nPress Enter to return...")
            return
    except Exception as e:
        print(f"[ComboExecutor Error] Failed to parse combo: {e}")
        input("\nPress Enter to return...")
        return
        
    print(f"\n[Ready] Target window: '{window_title}' (Process: '{process_name}')")
    print("You have 3 seconds to switch focus to the game window...")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1.0)
        
    print(f"\n[ComboExecutor] Executing overlapping combo: '{combo_str}'")
    executor.execute_overlapping_combo(key_events)
    
    input("\nPress Enter to return to main menu...")

def run_playlist_mode(config_manager: ConfigManager, game_monitor: GameMonitor):
    window_title = config_manager.config.get("game_window", config.TARGET_GAME_WINDOW)
    process_name = config_manager.config.get("game_process", "")
    
    playlist_manager = ComboPlaylistManager()
    playlist_names = playlist_manager.get_playlist_names()
    
    if not playlist_names:
        print("[Playlist Mode Error] No playlists loaded. Check playlists.json.")
        input("\nPress Enter to return...")
        return
        
    selected_playlist = playlist_names[choice_idx] if 'choice_idx' in locals() else playlist_names[0] # dummy logic to keep original context but let's be careful: actually selected_playlist is choice dependent. Let's look at lines 136-174 block.
    # Wait, let's keep the target range precise! Let's check lines 136-174 first.
    # Ah, lines 136-137 are separate. Let's just modify the window_title / process_name and the print block separately.
    # Let's cancel this chunk and break it down.
    
    playlist_manager = ComboPlaylistManager()
    playlist_names = playlist_manager.get_playlist_names()
    
    if not playlist_names:
        print("[Playlist Mode Error] No playlists loaded. Check playlists.json.")
        input("\nPress Enter to return...")
        return
        
    print("\n" + "=" * 60)
    print("                     SELECT COMBO PLAYLIST                      ")
    print("=" * 60)
    for idx, name in enumerate(playlist_names, 1):
        print(f"  {idx}. {name:20} -> {playlist_manager.get_playlist(name)}")
    print("-" * 60)
    
    try:
        choice = input(f"Select a playlist (1-{len(playlist_names)}): ").strip()
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(playlist_names)):
            print("Invalid choice. Returning to menu.")
            return
    except (ValueError, IndexError):
        print("Invalid choice. Returning to menu.")
        return
        
    start_hk = config_manager.config.get("start_hotkey", "f9").lower()
    stop_hk = config_manager.config.get("stop_hotkey", "f10").lower()
    
    print("\n" + "=" * 60)
    print(f"               RUNNING PLAYLIST LOOP: {selected_playlist.upper()}            ")
    print("=" * 60)
    print(f"Target Window:  '{window_title}'")
    print(f"Game Process:   '{process_name}'")
    print(f"Frame Rate:     {config.FPS} FPS")
    print(f"Start Hotkey:   {start_hk.upper()}")
    print(f"Stop Hotkey:    {stop_hk.upper()}")
    print("-" * 60)
    
    executor = ComboExecutor(
        config_manager=config_manager,
        game_monitor=game_monitor,
        fps=config.FPS
    )
    mapper = InputMapper(config_manager)
    
    orchestrator = PlaylistOrchestrator(
        playlist_name=selected_playlist,
        playlist_manager=playlist_manager,
        executor=executor,
        mapper=mapper,
        game_monitor=game_monitor,
        fps=config.FPS
    )
    
    listener = WindowsHotkeyListener()
    try:
        listener.register_hotkey(start_hk, orchestrator.start)
        listener.register_hotkey(stop_hk, orchestrator.stop)
    except ValueError as e:
        print(f"[Error] {e}")
        return
        
    listener.start()
    
    print(f"Playlist loop service for '{selected_playlist}' is active.")
    print(f"Press {start_hk.upper()} to start, {stop_hk.upper()} to pause.")
    print("Press ENTER in this console to stop the service and return to main menu.")
    print("-" * 60)
    
    try:
        input()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        orchestrator.stop()
        print("[Playlist Bot] Playlist service stopped. Returned all virtual key states.")

def main():
    config_manager = ConfigManager()
    
    while True:
        # Reload config from file
        config_manager.config = config_manager.load_config()
        # Retrieve game process and window name from current config
        process_name = config_manager.config.get("game_process", "")
        window_title = config_manager.config.get("game_window", config.TARGET_GAME_WINDOW)
        
        # Instantiate GameMonitor with the latest config
        game_monitor = GameMonitor(config_manager)
        
        # Display Status
        print("\n" + "=" * 60)
        print("          FIGHTING GAME INPUT AUTOMATION TOOL MENU          ")
        print("=" * 60)
        print(f"  Target Window Title Match: '{window_title}'")
        print(f"  Target Process Name:       '{process_name}'")
        p2_side = "RIGHT (Facing Left)" if config_manager.config.get("is_player2_right", True) else "LEFT (Facing Right)"
        print(f"  Player 2 Side:             {p2_side}")
        print(f"  Game status:               " 
              f"Running: {'YES' if game_monitor.is_game_running() else 'NO'} | "
              f"Focused: {'YES' if game_monitor.is_game_focused() else 'NO'}")
        print("-" * 60)
        print("  1. Run Bot (Auto Sequence Loop with F9/F10 Hotkeys)")
        print("  2. Configure Player 2 Key Bindings & Target Game")
        print("  3. Input and Execute Custom Combo Sequence")
        print("  4. Run Combo Playlist Loop (Randomized Orchestrator)")
        print("  5. Edit Combo Playlists (CRUD Editor)")
        print("  6. Exit")
        print("=" * 60)
        
        choice = input("Select an option (1-6): ").strip()
        
        if choice == '1':
            run_bot_mode(config_manager, game_monitor)
        elif choice == '2':
            config_manager.configure_bindings_cli()
            # ConfigManager saves automatically, loop will reload on next iteration
        elif choice == '3':
            execute_custom_combo_mode(config_manager, game_monitor)
        elif choice == '4':
            run_playlist_mode(config_manager, game_monitor)
        elif choice == '5':
            ComboPlaylistManager().manage_playlists_cli()
        elif choice == '6':
            print("Exiting tool. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")

if __name__ == "__main__":
    main()
