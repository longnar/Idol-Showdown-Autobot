mod api;
mod overlay;
mod ui;

use api::{ApiClient, Combo};
use overlay::OverlayController;
use ui::{ActiveField, AppState, InputMode};

use std::{
    io,
    process::{Child, Command, Stdio},
    time::{Duration, Instant},
};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Initialize API Client
    let api_client = ApiClient::new();

    // 2. Start Python Backend if not already running
    let mut backend_process: Option<Child> = None;
    if !api_client.check_alive().await {
        println!("[TUI Init] Python backend API is not running. Launching backend server...");
        
        let python_exe = if std::path::Path::new(".venv/Scripts/python.exe").exists() {
            ".venv/Scripts/python.exe"
        } else if std::path::Path::new("venv/Scripts/python.exe").exists() {
            "venv/Scripts/python.exe"
        } else {
            "python"
        };

        match Command::new(python_exe)
            .arg("run_backend.py")
            .env("TUI_MODE", "1")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
        {
            Ok(child) => {
                println!("[TUI Init] Spawned Python backend daemon (PID: {}).", child.id());
                backend_process = Some(child);
                
                // Wait for the backend to start
                println!("[TUI Init] Waiting for API server to boot...");
                for _ in 0..15 {
                    tokio::time::sleep(Duration::from_millis(500)).await;
                    if api_client.check_alive().await {
                        println!("[TUI Init] API Server connected!");
                        break;
                    }
                }
            }
            Err(e) => {
                eprintln!("[TUI Error] Failed to auto-launch Python backend: {}", e);
                eprintln!("Please make sure Python is installed and run 'python run_backend.py' manually.");
                return Ok(());
            }
        }
    } else {
        println!("[TUI Init] Detected running backend API server. Connecting...");
    }

    // Double check connection
    if !api_client.check_alive().await {
        eprintln!("[TUI Error] Could not connect to the Python Backend API server on port 5000.");
        if let Some(mut child) = backend_process {
            let _ = child.kill();
        }
        return Ok(());
    }

    // 3. Setup Terminal TUI
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // 4. Initialize State and Overlay
    let mut app = AppState::new();
    let overlay = OverlayController::new();
    overlay.hide();

    // Fetch initial data from API
    fetch_data(&api_client, &mut app).await;

    // 5. Main loop variables
    let mut last_tick = Instant::now();
    let tick_rate = Duration::from_millis(150); // Tick rate for UI refresh and API polling
    let mut api_poll_counter = 0;

    // 6. TUI Event Loop
    loop {
        // Draw TUI
        terminal.draw(|f| ui::draw_ui(f, &mut app))?;

        // Calculate timeout for blocking key event listener
        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));

        if event::poll(timeout)? {
            match event::read()? {
                Event::Key(key) => {
                    if key.kind == event::KeyEventKind::Press {
                        // Global hotkeys (ESC to close dialogs, Q to Quit)
                        if app.input_mode == InputMode::Normal {
                            match key.code {
                                KeyCode::Char('q') | KeyCode::Char('Q') => {
                                    break;
                                }
                                KeyCode::Esc => {
                                    app.show_new_playlist_dialog = false;
                                    app.show_new_combo_dialog = false;
                                    app.message = None;
                                }
                                KeyCode::Char('1') => app.active_tab = 0,
                                KeyCode::Char('2') => {
                                    app.active_tab = 1;
                                    app.menu_index = 0;
                                }
                                KeyCode::Char('3') => {
                                    app.active_tab = 2;
                                    app.menu_index = 0;
                                }
                                KeyCode::Char('4') => {
                                    app.active_tab = 3;
                                    app.menu_index = 0;
                                }
                                // Tab 1 (Dashboard) Controls
                                KeyCode::Char(' ') if app.active_tab == 0 => {
                                    // Toggle Bot Start/Stop
                                    if app.settings.gameStatus == "Active" {
                                        if let Ok(_) = api_client.stop_bot().await {
                                            app.settings.gameStatus = "Stopped".to_string();
                                        }
                                    } else {
                                        if let Ok(_) = api_client.start_bot().await {
                                            app.settings.gameStatus = "Active".to_string();
                                        }
                                    }
                                    fetch_data(&api_client, &mut app).await;
                                }
                                KeyCode::Char('r') | KeyCode::Char('R') if app.active_tab == 0 => {
                                    // Start combo recording
                                    if !app.record_status.recording {
                                        if let Ok(success) = api_client.start_record().await {
                                            if success {
                                                app.record_status.recording = true;
                                                overlay.set_text("");
                                                overlay.show();
                                            }
                                        }
                                    }
                                }
                                KeyCode::Char('s') | KeyCode::Char('S') if app.active_tab == 0 => {
                                    // Stop and save combo recording
                                    if app.record_status.recording {
                                        if let Ok(Some(recorded_combo)) = api_client.stop_record().await {
                                            app.record_status.recording = false;
                                            overlay.hide();
                                            
                                            if !recorded_combo.is_empty() {
                                                // Open dialog to save combo
                                                app.input_buffer = "".to_string();
                                                app.show_new_combo_dialog = true;
                                                app.active_field = Some(ActiveField::NewComboName);
                                                app.input_mode = InputMode::EditingValue;
                                                // Store the temporary combo to save later
                                                app.recorded_combo_to_save = Some(Combo {
                                                    id: None,
                                                    name: "New Combo".to_string(),
                                                    input: recorded_combo,
                                                    playlist: app.settings.selectedComboSet.clone(),
                                                });
                                            } else {
                                                app.message = Some("No combo keys were recorded.".to_string());
                                            }
                                        }
                                    }
                                }
                                KeyCode::Char('c') | KeyCode::Char('C') if app.active_tab == 0 => {
                                    // Cancel combo recording
                                    if app.record_status.recording {
                                        if let Ok(_) = api_client.cancel_record().await {
                                            app.record_status.recording = false;
                                            overlay.hide();
                                        }
                                    }
                                }
                                // Tab 2 (Playlists) Controls
                                KeyCode::Char('a') | KeyCode::Char('A') if app.active_tab == 1 => {
                                    // Create playlist
                                    app.input_buffer = "".to_string();
                                    app.show_new_playlist_dialog = true;
                                    app.active_field = Some(ActiveField::NewPlaylistName);
                                    app.input_mode = InputMode::EditingValue;
                                }
                                KeyCode::Char('c') | KeyCode::Char('C') if app.active_tab == 1 => {
                                    // Add combo to selected playlist
                                    if !app.playlists.is_empty() {
                                        app.input_buffer = "".to_string();
                                        app.show_new_combo_dialog = true;
                                        app.active_field = Some(ActiveField::NewComboName);
                                        app.input_mode = InputMode::EditingValue;
                                    }
                                }
                                KeyCode::Char('d') | KeyCode::Char('D') if app.active_tab == 1 => {
                                    // Delete combo
                                    let selected_pl_name = app.playlists.get(app.playlist_index);
                                    if let Some(pl_name) = selected_pl_name {
                                        let pl_combos: Vec<&Combo> = app.combos
                                            .iter()
                                            .filter(|c| c.playlist == *pl_name)
                                            .collect();
                                        if let Some(combo_to_delete) = pl_combos.get(app.combo_index) {
                                            if let Some(id) = &combo_to_delete.id {
                                                let _ = api_client.delete_combo(id).await;
                                                fetch_data(&api_client, &mut app).await;
                                                app.combo_index = 0;
                                            }
                                        }
                                    }
                                }
                                KeyCode::Char('p') | KeyCode::Char('P') if app.active_tab == 1 => {
                                    // Select active playlist
                                    if let Some(pl_name) = app.playlists.get(app.playlist_index) {
                                        app.settings.selectedComboSet = pl_name.clone();
                                        let _ = api_client.save_config(&app.settings).await;
                                        fetch_data(&api_client, &mut app).await;
                                    }
                                }
                                // Navigation controls
                                KeyCode::Up => {
                                    if app.active_tab == 1 {
                                        // Playlist or Combo list navigation
                                        // If focus is on playlist list vs combo list (we simplify by just navigating combo list, or playlist list if combos empty)
                                        if app.combo_index > 0 {
                                            app.combo_index -= 1;
                                        } else if app.playlist_index > 0 {
                                            app.playlist_index -= 1;
                                            app.combo_index = 0;
                                        }
                                    } else if app.menu_index > 0 {
                                        app.menu_index -= 1;
                                    }
                                }
                                KeyCode::Down => {
                                    if app.active_tab == 1 {
                                        let selected_pl_name = app.playlists.get(app.playlist_index);
                                        let combos_len = if let Some(pl_name) = selected_pl_name {
                                            app.combos.iter().filter(|c| c.playlist == *pl_name).count()
                                        } else {
                                            0
                                        };
                                        
                                        if app.combo_index + 1 < combos_len {
                                            app.combo_index += 1;
                                        } else if app.playlist_index + 1 < app.playlists.len() {
                                            app.playlist_index += 1;
                                            app.combo_index = 0;
                                        }
                                    } else {
                                        let max_idx = if app.active_tab == 2 { 5 } else { 11 };
                                        if app.menu_index < max_idx {
                                            app.menu_index += 1;
                                        }
                                    }
                                }
                                KeyCode::Enter => {
                                    // Trigger edit mode for highlighted configuration/binding item
                                    if app.active_tab == 2 || app.active_tab == 3 {
                                        app.input_mode = InputMode::EditingValue;
                                        app.input_buffer = String::new();
                                        if app.active_tab == 3 {
                                            app.manual_bind = false;
                                        }
                                    }
                                }
                                _ => {}
                            }
                        } else if app.input_mode == InputMode::EditingValue {
                            if app.active_tab == 3 && !app.manual_bind {
                                // Key Binding press-to-bind listening mode
                                match key.code {
                                    KeyCode::Esc => {
                                        app.input_mode = InputMode::Normal;
                                    }
                                    KeyCode::Tab => {
                                        app.manual_bind = true;
                                        app.input_buffer = String::new();
                                    }
                                    _ => {
                                        if let Some(key_name) = keycode_to_string(key.code) {
                                            app.input_buffer = key_name;
                                            save_binding_item(&api_client, &mut app).await;
                                            app.input_mode = InputMode::Normal;
                                            fetch_data(&api_client, &mut app).await;
                                        }
                                    }
                                }
                            } else {
                                // Dialog/Input edit mode key handlers
                                match key.code {
                                    KeyCode::Char(c) => {
                                        if app.active_field != Some(ActiveField::NewComboPlaylist) {
                                            app.input_buffer.push(c);
                                        }
                                    }
                                    KeyCode::Backspace => {
                                        if app.active_field != Some(ActiveField::NewComboPlaylist) {
                                            app.input_buffer.pop();
                                        }
                                    }
                                    KeyCode::Up | KeyCode::Left if app.active_field == Some(ActiveField::NewComboPlaylist) => {
                                        if !app.playlists.is_empty() {
                                            if app.playlist_index > 0 {
                                                app.playlist_index -= 1;
                                            } else {
                                                app.playlist_index = app.playlists.len() - 1;
                                            }
                                        }
                                    }
                                    KeyCode::Down | KeyCode::Right if app.active_field == Some(ActiveField::NewComboPlaylist) => {
                                        if !app.playlists.is_empty() {
                                            if app.playlist_index + 1 < app.playlists.len() {
                                                app.playlist_index += 1;
                                            } else {
                                                app.playlist_index = 0;
                                            }
                                        }
                                    }
                                    KeyCode::Esc => {
                                         if app.show_new_combo_dialog && app.active_tab == 0 {
                                             app.recorded_combo_to_save = None;
                                         }
                                         app.input_mode = InputMode::Normal;
                                         app.show_new_playlist_dialog = false;
                                         app.show_new_combo_dialog = false;
                                    }
                                    KeyCode::Tab if app.show_new_combo_dialog => {
                                        // Toggle combo dialog active fields
                                        if app.active_tab == 0 {
                                            if let Some(ActiveField::NewComboName) = app.active_field {
                                                app.active_field = Some(ActiveField::NewComboPlaylist);
                                            } else {
                                                app.active_field = Some(ActiveField::NewComboName);
                                            }
                                        } else {
                                            if let Some(ActiveField::NewComboName) = app.active_field {
                                                app.active_field = Some(ActiveField::NewComboInput);
                                            } else {
                                                app.active_field = Some(ActiveField::NewComboName);
                                            }
                                        }
                                    }
                                    KeyCode::Enter => {
                                        // Save editing field via API
                                        if app.show_new_playlist_dialog {
                                            if !app.input_buffer.trim().is_empty() {
                                                let _ = api_client.create_playlist(&app.input_buffer.trim().to_lowercase()).await;
                                                fetch_data(&api_client, &mut app).await;
                                            }
                                            app.show_new_playlist_dialog = false;
                                            app.input_mode = InputMode::Normal;
                                        } else if app.show_new_combo_dialog {
                                            if app.active_tab == 0 {
                                                 if let Some(ActiveField::NewComboName) = app.active_field {
                                                     // Save the name temporarily in the recorded combo
                                                     if let Some(ref mut combo) = app.recorded_combo_to_save {
                                                         combo.name = app.input_buffer.trim().to_string();
                                                     }
                                                     app.input_buffer = "".to_string();
                                                     app.active_field = Some(ActiveField::NewComboPlaylist);
                                                 } else if let Some(ActiveField::NewComboPlaylist) = app.active_field {
                                                     // Save recorded combo with chosen playlist
                                                     if let Some(mut combo) = app.recorded_combo_to_save.take() {
                                                         if let Some(pl) = app.playlists.get(app.playlist_index) {
                                                             combo.playlist = pl.clone();
                                                         }
                                                         let _ = api_client.save_combo(&combo).await;
                                                     }
                                                     app.show_new_combo_dialog = false;
                                                     app.input_mode = InputMode::Normal;
                                                     fetch_data(&api_client, &mut app).await;
                                                 }
                                            } else {
                                                if let Some(ActiveField::NewComboName) = app.active_field {
                                                    app.message = Some(app.input_buffer.clone()); // reuse message field as temp storage
                                                    app.input_buffer = "".to_string();
                                                    app.active_field = Some(ActiveField::NewComboInput);
                                                } else if let Some(ActiveField::NewComboInput) = app.active_field {
                                                    // Save manually entered combo
                                                    let name = app.message.clone().unwrap_or_else(|| "Manual Combo".to_string());
                                                    let input = app.input_buffer.clone();
                                                    let playlist = app.playlists.get(app.playlist_index).cloned().unwrap_or_default();
                                                    
                                                    let new_c = Combo {
                                                        id: None,
                                                        name,
                                                        input,
                                                        playlist,
                                                    };
                                                    let _ = api_client.save_combo(&new_c).await;
                                                    app.show_new_combo_dialog = false;
                                                    app.input_mode = InputMode::Normal;
                                                    app.message = None;
                                                    fetch_data(&api_client, &mut app).await;
                                                }
                                            }
                                        } else if app.active_tab == 2 {
                                            // Save App Configuration
                                            save_config_item(&api_client, &mut app).await;
                                            app.input_mode = InputMode::Normal;
                                            fetch_data(&api_client, &mut app).await;
                                        } else if app.active_tab == 3 {
                                            // Save Key Binding
                                            save_binding_item(&api_client, &mut app).await;
                                            app.input_mode = InputMode::Normal;
                                            fetch_data(&api_client, &mut app).await;
                                        }
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                }
                Event::Mouse(mouse_event) => {
                    if mouse_event.kind == event::MouseEventKind::Down(event::MouseButton::Left) {
                        let col = mouse_event.column;
                        let row = mouse_event.row;
                        if let Ok(term_size) = terminal.size() {
                            let size = ratatui::layout::Rect::new(0, 0, term_size.width, term_size.height);
                            // 1. Check Tabs Click (Header Row size.y + 1)
                            if row == size.y + 1 {
                                if col >= 2 && col <= 17 {
                                    app.active_tab = 0;
                                } else if col >= 20 && col <= 35 {
                                    app.active_tab = 1;
                                    app.menu_index = 0;
                                } else if col >= 38 && col <= 54 {
                                    app.active_tab = 2;
                                    app.menu_index = 0;
                                } else if col >= 57 && col <= 75 {
                                    app.active_tab = 3;
                                    app.menu_index = 0;
                                }
                            }

                            // 2. Handle clicks in Main Content area (from y = size.y + 3)
                            let y_start = size.y + 3;
                            if row >= y_start && row < size.y + size.height - 7 {
                                match app.active_tab {
                                    0 => {
                                        // Dashboard Tab: Right-panel actions box click handlers
                                        let chunks = ratatui::layout::Layout::default()
                                            .direction(ratatui::layout::Direction::Vertical)
                                            .constraints([
                                                ratatui::layout::Constraint::Length(3),
                                                ratatui::layout::Constraint::Min(10),
                                                ratatui::layout::Constraint::Length(7),
                                            ])
                                            .split(size);

                                        let dashboard_chunks = ratatui::layout::Layout::default()
                                            .direction(ratatui::layout::Direction::Horizontal)
                                            .constraints([ratatui::layout::Constraint::Percentage(50), ratatui::layout::Constraint::Percentage(50)])
                                            .split(chunks[1]);

                                        let right_chunks = ratatui::layout::Layout::default()
                                            .direction(ratatui::layout::Direction::Vertical)
                                            .constraints([ratatui::layout::Constraint::Min(0), ratatui::layout::Constraint::Length(6)])
                                            .split(dashboard_chunks[1]);

                                        let action_area = right_chunks[1];
                                        
                                        if col >= action_area.x && col < action_area.x + action_area.width
                                            && row >= action_area.y && row < action_area.y + action_area.height
                                        {
                                            let rel_row = row - action_area.y;
                                            let rel_col = col - action_area.x;
                                            
                                            if rel_row == 1 {
                                                if rel_col >= 1 && rel_col <= 15 {
                                                    // Toggle Bot
                                                    if app.settings.gameStatus == "Active" {
                                                        if let Ok(_) = api_client.stop_bot().await {
                                                            app.settings.gameStatus = "Stopped".to_string();
                                                        }
                                                    } else {
                                                        if let Ok(_) = api_client.start_bot().await {
                                                            app.settings.gameStatus = "Active".to_string();
                                                        }
                                                    }
                                                    fetch_data(&api_client, &mut app).await;
                                                } else if rel_col >= 18 && rel_col <= 34 {
                                                    // Record Combo
                                                    if !app.record_status.recording {
                                                        if let Ok(success) = api_client.start_record().await {
                                                            if success {
                                                                app.record_status.recording = true;
                                                                overlay.set_text("");
                                                                overlay.show();
                                                            }
                                                        }
                                                    }
                                                }
                                            } else if rel_row == 2 {
                                                if rel_col >= 1 && rel_col <= 15 {
                                                    // Save Combo
                                                    if app.record_status.recording {
                                                        if let Ok(Some(recorded_combo)) = api_client.stop_record().await {
                                                            app.record_status.recording = false;
                                                            overlay.hide();
                                                            
                                                             if !recorded_combo.is_empty() {
                                                                 app.input_buffer = "".to_string();
                                                                 app.show_new_combo_dialog = true;
                                                                 app.active_field = Some(ActiveField::NewComboName);
                                                                 app.input_mode = InputMode::EditingValue;
                                                                 app.recorded_combo_to_save = Some(Combo {
                                                                     id: None,
                                                                     name: "New Combo".to_string(),
                                                                     input: recorded_combo,
                                                                     playlist: app.settings.selectedComboSet.clone(),
                                                                 });
                                                             } else {
                                                                app.message = Some("No combo keys were recorded.".to_string());
                                                            }
                                                        }
                                                    }
                                                } else if rel_col >= 18 && rel_col <= 34 {
                                                    // Cancel Rec
                                                    if app.record_status.recording {
                                                        if let Ok(_) = api_client.cancel_record().await {
                                                            app.record_status.recording = false;
                                                            overlay.hide();
                                                        }
                                                    }
                                                }
                                            } else if rel_row == 3 {
                                                if rel_col >= 1 && rel_col <= 15 {
                                                    // Exit App
                                                    break;
                                                }
                                            } else if rel_row == 4 {
                                                // Toggle Global Hotkeys
                                                if rel_col >= 10 && rel_col <= 32 {
                                                    app.settings.hotkeysEnabled = !app.settings.hotkeysEnabled;
                                                    let _ = api_client.save_config(&app.settings).await;
                                                    fetch_data(&api_client, &mut app).await;
                                                }
                                            }
                                        }
                                    }
                                    1 => {
                                        // Playlists Tab
                                        if col < size.width * 30 / 100 {
                                            // Left panel: Playlists list
                                            if row >= y_start + 1 {
                                                let clicked_idx = (row - y_start - 1) as usize;
                                                if clicked_idx < app.playlists.len() {
                                                    app.playlist_index = clicked_idx;
                                                    app.combo_index = 0;
                                                }
                                            }
                                        } else {
                                            // Right panel: Combos list
                                            if row >= y_start + 3 {
                                                let selected_pl_name = app.playlists.get(app.playlist_index);
                                                if let Some(pl_name) = selected_pl_name {
                                                    let pl_combos_len = app.combos.iter().filter(|c| c.playlist == *pl_name).count();
                                                    let clicked_idx = (row - y_start - 3) as usize;
                                                    if clicked_idx < pl_combos_len {
                                                        app.combo_index = clicked_idx;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    2 => {
                                        // App Config Tab: click rows to edit
                                        if row >= y_start + 1 {
                                            let clicked_idx = (row - y_start - 1) as usize;
                                            if clicked_idx < 6 {
                                                app.menu_index = clicked_idx;
                                                app.input_mode = InputMode::EditingValue;
                                                app.input_buffer = String::new();
                                            }
                                        }
                                    }
                                    3 => {
                                        // Key Bindings Tab: click rows to edit
                                        if row >= y_start + 1 {
                                            let clicked_idx = (row - y_start - 1) as usize;
                                            if clicked_idx < 12 {
                                                app.menu_index = clicked_idx;
                                                app.input_mode = InputMode::EditingValue;
                                                app.input_buffer = String::new();
                                                app.manual_bind = false;
                                            }
                                        }
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        // 7. Polling logic (Runs every 150ms tick)
        if last_tick.elapsed() >= tick_rate {
            last_tick = Instant::now();
            
            // Poll API states
            api_poll_counter += 1;
            
            // Poll game status and logs every tick (150ms)
            if let Ok(st) = api_client.get_status().await {
                app.game_status = st;
            }
            if let Ok(lg) = api_client.get_logs().await {
                app.logs = lg;
            }
            if let Ok(bot_st) = api_client.get_bot_status().await {
                app.settings.gameStatus = if bot_st.running { "Active".to_string() } else { "Stopped".to_string() };
                if let Some(pl) = bot_st.active_playlist {
                    app.settings.selectedComboSet = pl;
                }
            }

            // Every 5 ticks (750ms), poll all playlist data & configs
            if api_poll_counter >= 5 {
                api_poll_counter = 0;
                fetch_data(&api_client, &mut app).await;
            }

            // If recording, poll the live string very frequently and update the Win32 overlay text
            if app.record_status.recording {
                if let Ok(rec_st) = api_client.get_record_status().await {
                    app.record_status = rec_st;
                    if let Some(live) = &app.record_status.live_combo {
                        overlay.set_text(live);
                    }
                }
            }
        }
    }

    // 8. Cleanup and Exit
    overlay.close();
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    // Shutdown backend process if spawned by us
    if let Some(mut child) = backend_process {
        println!("[TUI Clean] Stopping Python backend process (PID: {})...", child.id());
        let _ = child.kill();
    }

    println!("[TUI Clean] Application exited successfully.");
    Ok(())
}

async fn fetch_data(api_client: &ApiClient, app: &mut AppState) {
    if let Ok(cfg) = api_client.get_config().await {
        app.settings = cfg.settings;
        app.bindings = cfg.bindings;
    }
    if let Ok(combos_data) = api_client.get_combos().await {
        app.combos = combos_data.combos;
        app.playlists = combos_data.playlists;
    }
}

async fn save_config_item(api_client: &ApiClient, app: &mut AppState) {
    let input = app.input_buffer.trim();
    if input.is_empty() { return; }

    match app.menu_index {
        0 => app.settings.gameProcess = input.to_string(),
        1 => app.settings.gameWindow = input.to_string(),
        2 => {
            if let Ok(val) = input.parse::<u32>() {
                app.settings.delayFrames = val;
            }
        }
        3 => {
            let parsed = input.to_uppercase();
            app.settings.isPlayer2Right = parsed.starts_with('R') || parsed.starts_with('Y') || parsed.starts_with('1');
        }
        4 => app.settings.startHotkey = input.to_string(),
        5 => app.settings.stopHotkey = input.to_string(),
        _ => {}
    }

    let _ = api_client.save_config(&app.settings).await;
}

async fn save_binding_item(api_client: &ApiClient, app: &mut AppState) {
    let input = app.input_buffer.trim().to_lowercase();
    if input.is_empty() { return; }

    match app.menu_index {
        0 => app.bindings.Crouch = input,
        1 => app.bindings.Jump = input,
        2 => app.bindings.Left = input,
        3 => app.bindings.Right = input,
        4 => app.bindings.Light = input,
        5 => app.bindings.Medium = input,
        6 => app.bindings.Heavy = input,
        7 => app.bindings.Special = input,
        8 => app.bindings.Burst = input,
        9 => app.bindings.Collab = input,
        10 => app.bindings.Items = input,
        11 => app.bindings.Grab = input,
        _ => {}
    }

    let _ = api_client.save_bindings(&app.bindings).await;
}

fn keycode_to_string(code: KeyCode) -> Option<String> {
    match code {
        KeyCode::Char(' ') => Some("space".to_string()),
        KeyCode::Char(c) => Some(c.to_lowercase().to_string()),
        KeyCode::Up => Some("up".to_string()),
        KeyCode::Down => Some("down".to_string()),
        KeyCode::Left => Some("left".to_string()),
        KeyCode::Right => Some("right".to_string()),
        KeyCode::Esc => Some("esc".to_string()),
        KeyCode::Enter => Some("enter".to_string()),
        KeyCode::Backspace => Some("backspace".to_string()),
        KeyCode::Tab => Some("tab".to_string()),
        _ => None,
    }
}
