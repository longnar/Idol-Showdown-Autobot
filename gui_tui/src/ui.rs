use crate::api::{Combo, GameStatus, LogEntry, RecordStatus, Settings, Bindings};
use ratatui::{
    backend::Backend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Row, Table, Tabs},
    Frame,
};

#[derive(PartialEq)]
pub enum InputMode {
    Normal,
    EditingValue,
}

#[derive(PartialEq, Clone, Copy, Debug)]
pub enum ActiveField {
    // Config editing fields
    GameProcess,
    GameWindow,
    DelayFrames,
    P2Side,
    StartHotkey,
    StopHotkey,
    // Binding fields
    BindJump, BindCrouch, BindLeft, BindRight,
    BindLight, BindMedium, BindHeavy, BindSpecial,
    BindBurst, BindCollab, BindItems, BindGrab,
    // Add Playlist/Combo fields
    NewPlaylistName,
    NewComboName,
    NewComboInput,
    NewComboPlaylist,
}

pub struct AppState {
    pub active_tab: usize,
    pub game_status: GameStatus,
    pub settings: Settings,
    pub bindings: Bindings,
    pub playlists: Vec<String>,
    pub combos: Vec<Combo>,
    pub logs: Vec<LogEntry>,
    pub record_status: RecordStatus,
    pub recorded_combo_to_save: Option<Combo>,
    
    // UI selection indexes
    pub menu_index: usize, // index of active field in Config or Bindings
    pub playlist_index: usize, // index of selected playlist
    pub combo_index: usize, // index of selected combo in playlist
    
    // Inputs
    pub input_mode: InputMode,
    pub input_buffer: String,
    pub manual_bind: bool,
    pub active_field: Option<ActiveField>,
    
    // Dialog state
    pub show_new_playlist_dialog: bool,
    pub show_new_combo_dialog: bool,
    pub message: Option<String>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            active_tab: 0,
            game_status: GameStatus::default(),
            settings: Settings::default(),
            bindings: Bindings::default(),
            playlists: Vec::new(),
            combos: Vec::new(),
            logs: Vec::new(),
            record_status: RecordStatus::default(),
            recorded_combo_to_save: None,
            menu_index: 0,
            playlist_index: 0,
            combo_index: 0,
            input_mode: InputMode::Normal,
            input_buffer: String::new(),
            manual_bind: false,
            active_field: None,
            show_new_playlist_dialog: false,
            show_new_combo_dialog: false,
            message: None,
        }
    }
}

pub fn draw_ui(f: &mut Frame, app: &mut AppState) {
    let size = f.size();

    // Main layout: Title/Tabs, Main content area, Logs area (bottom)
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Tabs
            Constraint::Min(10),   // Main Content
            Constraint::Length(7), // Diagnostics Logs
        ])
        .split(size);

    // --- 1. Draw Title & Tabs ---
    let titles = vec!["[1] DASHBOARD", "[2] PLAYLISTS", "[3] APP CONFIG", "[4] KEY BINDINGS"];
    let tab_titles = titles
        .iter()
        .map(|t| Line::from(Span::styled(*t, Style::default().fg(Color::LightCyan))))
        .collect::<Vec<_>>();

    let tabs = Tabs::new(tab_titles)
        .block(
            Block::default()
                .title(" IDOL SHOWDOWN AUTOBOT (V0.1 TUI) ")
                .title_alignment(ratatui::layout::Alignment::Center)
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        )
        .select(app.active_tab)
        .highlight_style(
            Style::default()
                .fg(Color::Black)
                .bg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        );
    f.render_widget(tabs, chunks[0]);

    // --- 2. Draw Main Content based on active tab ---
    match app.active_tab {
        0 => draw_dashboard(f, app, chunks[1]),
        1 => draw_playlists(f, app, chunks[1]),
        2 => draw_config(f, app, chunks[1]),
        3 => draw_bindings(f, app, chunks[1]),
        _ => {}
    }

    // --- 3. Draw Log Panel (Bottom) ---
    draw_logs(f, app, chunks[2]);

    // --- 4. Draw overlays/dialogs if active ---
    if app.show_new_playlist_dialog {
        draw_new_playlist_dialog(f, app, size);
    } else if app.show_new_combo_dialog {
        draw_new_combo_dialog(f, app, size);
    } else if let Some(msg) = &app.message {
        draw_message_dialog(f, msg, size);
    }
}

fn draw_dashboard(f: &mut Frame, app: &AppState, area: Rect) {
    let dashboard_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    // Left Panel: Game & Bot Status
    let game_run_str = if app.game_status.game_running { "YES" } else { "NO" };
    let game_focus_str = if app.game_status.game_focused { "YES" } else { "NO" };
    let game_run_color = if app.game_status.game_running { Color::Green } else { Color::Red };
    let game_focus_color = if app.game_status.game_focused { Color::Green } else { Color::Yellow };
    
    let bot_run_str = if app.settings.gameStatus == "Active" { "RUNNING" } else { "STOPPED" };
    let bot_run_color = if app.settings.gameStatus == "Active" { Color::Green } else { Color::Red };

    let status_text = vec![
        Line::from(vec![
            Span::styled("Target Window:     ", Style::default().fg(Color::Gray)),
            Span::styled(format!("'{}'", app.game_status.game_window), Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Game Process:      ", Style::default().fg(Color::Gray)),
            Span::styled(format!("'{}'", app.game_status.game_process), Style::default().fg(Color::White)),
        ]),
        Line::from(vec![
            Span::styled("Game Running:      ", Style::default().fg(Color::Gray)),
            Span::styled(game_run_str, Style::default().fg(game_run_color).add_modifier(Modifier::BOLD)),
            Span::styled(format!(" (PID: {:?})", app.game_status.game_pid.unwrap_or(0)), Style::default().fg(Color::DarkGray)),
        ]),
        Line::from(vec![
            Span::styled("Game Focused:      ", Style::default().fg(Color::Gray)),
            Span::styled(game_focus_str, Style::default().fg(game_focus_color).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Player 2 Side:     ", Style::default().fg(Color::Gray)),
            Span::styled(
                if app.settings.isPlayer2Right { "RIGHT (Facing Left)" } else { "LEFT (Facing Right)" },
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
            ),
        ]),
        Line::from(""),
        Line::from(vec![
            Span::styled("================= BOT SERVICE =================\n", Style::default().fg(Color::DarkGray)),
        ]),
        Line::from(vec![
            Span::styled("Bot Service:       ", Style::default().fg(Color::Gray)),
            Span::styled(bot_run_str, Style::default().fg(bot_run_color).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Active Playlist:   ", Style::default().fg(Color::Gray)),
            Span::styled(format!("'{}'", app.settings.selectedComboSet.to_uppercase()), Style::default().fg(Color::LightMagenta).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Hotkeys registered: ", Style::default().fg(Color::Gray)),
            Span::styled(format!("START={} | PAUSE={}", app.settings.startHotkey.upper_hex(), app.settings.stopHotkey.upper_hex()), Style::default().fg(Color::LightCyan)),
        ]),
    ];

    let status_widget = Paragraph::new(status_text)
        .block(
            Block::default()
                .title(" STATUS DIAGNOSTICS ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        );
    f.render_widget(status_widget, dashboard_chunks[0]);

    // Right Panel: Combo Recording Controls & Instructions split vertically
    let right_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(0), Constraint::Length(6)])
        .split(dashboard_chunks[1]);

    let live_str = app.record_status.live_combo.clone().unwrap_or_default();
    let display_live = if live_str.chars().count() > 25 {
        let skip_count = live_str.chars().count() - 22;
        format!("...{}", live_str.chars().skip(skip_count).collect::<String>())
    } else {
        live_str
    };
    let rec_state = if app.record_status.recording {
        format!("● RECORDING (Live: {})", display_live)
    } else {
        "IDLE".to_string()
    };
    let rec_color = if app.record_status.recording { Color::Red } else { Color::Gray };

    let control_text = vec![
        Line::from(vec![
            Span::styled("=== COMBO RECORDING OVERLAY (HYBRID) ===", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(""),
        Line::from(vec![
            Span::styled("Recording State:   ", Style::default().fg(Color::Gray)),
            Span::styled(rec_state, Style::default().fg(rec_color).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(""),
        Line::from(vec![
            Span::styled("Press 'R' ", Style::default().fg(Color::LightCyan).add_modifier(Modifier::BOLD)),
            Span::styled("to START recording combo (Spawns win32 overlay)", Style::default().fg(Color::White)),
        ]),
        Line::from(vec![
            Span::styled("Press 'S' ", Style::default().fg(Color::LightGreen).add_modifier(Modifier::BOLD)),
            Span::styled("to SAVE recorded combo", Style::default().fg(Color::White)),
        ]),
        Line::from(vec![
            Span::styled("Press 'C' ", Style::default().fg(Color::LightRed).add_modifier(Modifier::BOLD)),
            Span::styled("to CANCEL/RESET recording", Style::default().fg(Color::White)),
        ]),
    ];

    let control_widget = Paragraph::new(control_text)
        .block(
            Block::default()
                .title(" BOT CONTROL INTERFACE ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        );
    f.render_widget(control_widget, right_chunks[0]);

    // Bottom Right Panel: Interactive Operations & Hotkey Toggles (Compact 2-Column layout)
    let hotkeys_status_str = if app.settings.hotkeysEnabled { "ACTIVE (ON)" } else { "DISABLED (OFF)" };
    let hotkeys_status_color = if app.settings.hotkeysEnabled { Color::Green } else { Color::Red };

    let quick_actions_text = vec![
        Line::from(vec![
            Span::styled(" [Toggle Bot] ", Style::default().fg(Color::Black).bg(Color::LightGreen).add_modifier(Modifier::BOLD)),
            Span::raw("   "),
            Span::styled(" [Record Combo] ", Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled(" [Save Combo] ", Style::default().fg(Color::Black).bg(Color::LightYellow).add_modifier(Modifier::BOLD)),
            Span::raw("   "),
            Span::styled(" [Cancel Rec]   ", Style::default().fg(Color::Black).bg(Color::LightRed).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled(" [Exit App]     ", Style::default().fg(Color::White).bg(Color::Red).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::raw(" Hotkeys: "),
            Span::styled(format!(" [{}] ", hotkeys_status_str), Style::default().fg(Color::Black).bg(hotkeys_status_color).add_modifier(Modifier::BOLD)),
        ]),
    ];

    let quick_actions_widget = Paragraph::new(quick_actions_text)
        .block(
            Block::default()
                .title(" QUICK OPERATIONS & HOTKEYS ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        );
    f.render_widget(quick_actions_widget, right_chunks[1]);
}

fn draw_playlists(f: &mut Frame, app: &AppState, area: Rect) {
    let pl_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(30), Constraint::Percentage(70)])
        .split(area);

    // Left sub-panel: Playlist Names
    let pl_items: Vec<ListItem> = app.playlists
        .iter()
        .enumerate()
        .map(|(i, name)| {
            let style = if i == app.playlist_index {
                Style::default().fg(Color::Black).bg(Color::Magenta).add_modifier(Modifier::BOLD)
            } else if app.settings.selectedComboSet == *name {
                Style::default().fg(Color::LightMagenta).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::White)
            };
            
            let display_name = if app.settings.selectedComboSet == *name {
                format!("★ {}", name.upper_hex())
            } else {
                format!("  {}", name.upper_hex())
            };
            ListItem::new(Line::from(Span::styled(display_name, style)))
        })
        .collect();

    let pl_list = List::new(pl_items)
        .block(
            Block::default()
                .title(" PLAYLISTS (A: Add, ★: Active) ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Magenta)),
        );
    f.render_widget(pl_list, pl_chunks[0]);

    // Right sub-panel: Combos in Selected Playlist
    let selected_playlist_name = app.playlists.get(app.playlist_index);
    let mut combo_rows = Vec::new();

    if let Some(pl_name) = selected_playlist_name {
        let pl_combos: Vec<&Combo> = app.combos
            .iter()
            .filter(|c| c.playlist == *pl_name)
            .collect();

        for (i, c) in pl_combos.iter().enumerate() {
            let style = if i == app.combo_index {
                Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::White)
            };

            combo_rows.push(Row::new(vec![
                Span::styled(c.name.clone(), style),
                Span::styled(c.input.clone(), style),
            ]));
        }
    }

    let combo_table = Table::new(
        combo_rows,
        [Constraint::Percentage(30), Constraint::Percentage(70)]
    )
    .header(
        Row::new(vec![
            Span::styled("Combo Name", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::styled("Numpad Notation / Input Sequence", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ])
        .bottom_margin(1)
    )
    .block(
        Block::default()
            .title(format!(" COMBOS IN PLAYLIST: '{}' (C: Add Combo, D: Delete Combo) ", selected_playlist_name.unwrap_or(&"NONE".to_string()).to_uppercase()))
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan)),
    );
    f.render_widget(combo_table, pl_chunks[1]);
}

fn draw_config(f: &mut Frame, app: &AppState, area: Rect) {
    let fields = vec![
        ("1. Target Game Process", app.settings.gameProcess.clone(), ActiveField::GameProcess),
        ("2. Target Window Title", app.settings.gameWindow.clone(), ActiveField::GameWindow),
        ("3. Delay Frames", app.settings.delayFrames.to_string(), ActiveField::DelayFrames),
        ("4. Player 2 Side (L/R)", if app.settings.isPlayer2Right { "RIGHT".to_string() } else { "LEFT".to_string() }, ActiveField::P2Side),
        ("5. Start Bot Hotkey", app.settings.startHotkey.upper_hex(), ActiveField::StartHotkey),
        ("6. Stop Bot Hotkey", app.settings.stopHotkey.upper_hex(), ActiveField::StopHotkey),
    ];

    let mut rows = Vec::new();
    for (i, (label, val, _field)) in fields.iter().enumerate() {
        let is_selected = i == app.menu_index;
        
        let label_style = if is_selected {
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };

        let val_style = if is_selected && app.input_mode == InputMode::EditingValue {
            Style::default().fg(Color::Black).bg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else if is_selected {
            Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::LightYellow)
        };

        let display_val = if is_selected && app.input_mode == InputMode::EditingValue {
            format!("{}█", app.input_buffer)
        } else {
            val.clone()
        };

        rows.push(Row::new(vec![
            Span::styled(*label, label_style),
            Span::styled(display_val, val_style),
        ]));
    }

    let config_table = Table::new(
        rows,
        [Constraint::Percentage(40), Constraint::Percentage(60)]
    )
    .block(
        Block::default()
            .title(" CONFIGURATION MENU (Enter to edit, Esc to save/cancel) ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan)),
    );

    f.render_widget(config_table, area);
}

fn draw_bindings(f: &mut Frame, app: &AppState, area: Rect) {
    let b = &app.bindings;
    let fields = vec![
        ("1. Crouch (Down)", b.Crouch.clone(), ActiveField::BindCrouch),
        ("2. Jump (Up)", b.Jump.clone(), ActiveField::BindJump),
        ("3. Left", b.Left.clone(), ActiveField::BindLeft),
        ("4. Right", b.Right.clone(), ActiveField::BindRight),
        ("5. Light Attack", b.Light.clone(), ActiveField::BindLight),
        ("6. Medium Attack", b.Medium.clone(), ActiveField::BindMedium),
        ("7. Heavy Attack", b.Heavy.clone(), ActiveField::BindHeavy),
        ("8. Special Attack", b.Special.clone(), ActiveField::BindSpecial),
        ("9. Burst", b.Burst.clone(), ActiveField::BindBurst),
        ("10. Collab", b.Collab.clone(), ActiveField::BindCollab),
        ("11. Items", b.Items.clone(), ActiveField::BindItems),
        ("12. Grab", b.Grab.clone(), ActiveField::BindGrab),
    ];

    let mut rows = Vec::new();
    for (i, (label, val, _field)) in fields.iter().enumerate() {
        let is_selected = i == app.menu_index;
        
        let label_style = if is_selected {
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };

        let val_style = if is_selected && app.input_mode == InputMode::EditingValue {
            Style::default().fg(Color::Black).bg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else if is_selected {
            Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::LightYellow)
        };

        let display_val = if is_selected && app.input_mode == InputMode::EditingValue {
            if !app.manual_bind {
                "[ PRESS KEY (Tab to type) ]".to_string()
            } else {
                format!("{}█", app.input_buffer)
            }
        } else {
            val.clone().to_uppercase()
        };

        rows.push(Row::new(vec![
            Span::styled(*label, label_style),
            Span::styled(display_val, val_style),
        ]));
    }

    let bindings_table = Table::new(
        rows,
        [Constraint::Percentage(50), Constraint::Percentage(50)]
    )
    .block(
        Block::default()
            .title(" PLAYER 2 VIRTUAL KEY BINDINGS (Enter to edit, Esc to save/cancel) ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan)),
    );

    f.render_widget(bindings_table, area);
}

fn draw_logs(f: &mut Frame, app: &AppState, area: Rect) {
    let log_lines = app.logs
        .iter()
        .rev() // Show newest at the bottom
        .take(5) // Max 5 lines
        .rev()
        .map(|entry| {
            let log_color = match entry.r#type.as_str() {
                "success" => Color::Green,
                "error" => Color::Red,
                "warning" => Color::Yellow,
                _ => Color::Gray,
            };
            let prefix = format!("[{}] [{}] ", entry.timestamp, entry.r#type.to_uppercase());
            Line::from(vec![
                Span::styled(prefix, Style::default().fg(log_color).add_modifier(Modifier::BOLD)),
                Span::styled(entry.msg.clone(), Style::default().fg(Color::White)),
            ])
        })
        .collect::<Vec<_>>();

    let logs_widget = Paragraph::new(log_lines)
        .block(
            Block::default()
                .title(" LIVE DIAGNOSTICS LOGS ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray)),
        );
    f.render_widget(logs_widget, area);
}

// Dialog boxes

fn draw_new_playlist_dialog(f: &mut Frame, app: &AppState, area: Rect) {
    let text = vec![
        Line::from("Enter Name for the New Playlist:"),
        Line::from(""),
        Line::from(Span::styled(format!("  {}█", app.input_buffer), Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from("Press Enter to Confirm, Esc to Cancel."),
    ];

    let p = Paragraph::new(text)
        .block(
            Block::default()
                .title(" NEW PLAYLIST ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Magenta)),
        );

    let popup_area = center_rect(50, 30, area);
    f.render_widget(Clear, popup_area);
    f.render_widget(p, popup_area);
}

fn draw_new_combo_dialog(f: &mut Frame, app: &AppState, area: Rect) {
    let text = if app.active_tab == 0 {
        // Tab 0: Saving recorded combo
        let focus_field = match &app.active_field {
            Some(ActiveField::NewComboName) => "Name",
            Some(ActiveField::NewComboPlaylist) => "Playlist",
            _ => "",
        };

        let selected_playlist_name = app.playlists.get(app.playlist_index).cloned().unwrap_or_default();
        let preview_input = app.recorded_combo_to_save.as_ref().map(|c| c.input.as_str()).unwrap_or("");
        
        vec![
            Line::from("Save Recorded Combo:"),
            Line::from(""),
            Line::from(vec![
                Span::styled("1. Name:     ", Style::default().fg(Color::Gray)),
                Span::styled(
                    if focus_field == "Name" {
                        format!("{}█", app.input_buffer)
                    } else {
                        app.recorded_combo_to_save.as_ref().map(|c| c.name.clone()).unwrap_or_default()
                    }, 
                    if focus_field == "Name" { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::White) }
                ),
            ]),
            Line::from(vec![
                Span::styled("2. Playlist: ", Style::default().fg(Color::Gray)),
                Span::styled(
                    if focus_field == "Playlist" { format!("< {} >", selected_playlist_name) } else { selected_playlist_name }, 
                    if focus_field == "Playlist" { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::White) }
                ),
            ]),
            Line::from(""),
            Line::from(vec![
                Span::styled("Input Preview: ", Style::default().fg(Color::DarkGray)),
                Span::styled(preview_input, Style::default().fg(Color::DarkGray)),
            ]),
            Line::from(""),
            Line::from("Press Tab to toggle fields, Arrow keys to cycle Playlist, Enter to Save, Esc to Cancel."),
        ]
    } else {
        // Tab 1: Creating manual combo
        let focus_field = match &app.active_field {
            Some(ActiveField::NewComboName) => "Name",
            Some(ActiveField::NewComboInput) => "Input Sequence",
            _ => "",
        };

        let temp_name = if focus_field == "Name" {
            format!("{}█", app.input_buffer)
        } else {
            app.message.clone().unwrap_or_default()
        };

        let temp_input = if focus_field == "Input Sequence" {
            format!("{}█", app.input_buffer)
        } else {
            "".to_string()
        };

        vec![
            Line::from("Create Manual Combo:"),
            Line::from(""),
            Line::from(vec![
                Span::styled("1. Name:   ", Style::default().fg(Color::Gray)),
                Span::styled(temp_name, if focus_field == "Name" { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::White) }),
            ]),
            Line::from(vec![
                Span::styled("2. Input:  ", Style::default().fg(Color::Gray)),
                Span::styled(temp_input, if focus_field == "Input Sequence" { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::White) }),
            ]),
            Line::from(""),
            Line::from("Press Tab to toggle fields, Enter to confirm/progress, Esc to Cancel."),
        ]
    };

    let p = Paragraph::new(text)
        .block(
            Block::default()
                .title(" ADD NEW COMBO ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        );

    let popup_area = center_rect(60, 40, area);
    f.render_widget(Clear, popup_area);
    f.render_widget(p, popup_area);
}

fn draw_message_dialog(f: &mut Frame, msg: &str, area: Rect) {
    let text = vec![
        Line::from(msg),
        Line::from(""),
        Line::from(Span::styled("Press ESC to close.", Style::default().fg(Color::Cyan))),
    ];

    let p = Paragraph::new(text)
        .block(
            Block::default()
                .title(" MESSAGE ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::LightRed)),
        );

    let popup_area = center_rect(50, 25, area);
    f.render_widget(Clear, popup_area);
    f.render_widget(p, popup_area);
}

// Helpers
fn center_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}

// Extends String to capitalize and uppercase hotkey string neatly
trait UpperHexExt {
    fn upper_hex(&self) -> String;
}

impl UpperHexExt for String {
    fn upper_hex(&self) -> String {
        self.to_uppercase()
    }
}
