use serde::{Deserialize, Serialize};
use std::collections::HashMap;

const BASE_URL: &str = "http://127.0.0.1:5000";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct GameStatus {
    pub game_running: bool,
    pub game_focused: bool,
    pub game_process: String,
    pub game_window: String,
    pub game_pid: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Settings {
    pub gameStatus: String,
    pub delayFrames: u32,
    pub isPlayer2Right: bool,
    pub selectedComboSet: String,
    pub startHotkey: String,
    pub stopHotkey: String,
    pub gameProcess: String,
    pub gameWindow: String,
    pub hotkeysEnabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Bindings {
    pub Jump: String,
    pub Crouch: String,
    pub Left: String,
    pub Right: String,
    pub Light: String,
    pub Medium: String,
    pub Heavy: String,
    pub Special: String,
    pub Burst: String,
    pub Collab: String,
    pub Items: String,
    pub Grab: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ConfigResponse {
    pub settings: Settings,
    pub bindings: Bindings,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Combo {
    pub id: Option<String>,
    pub name: String,
    pub input: String,
    pub playlist: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CombosResponse {
    pub combos: Vec<Combo>,
    pub playlists: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BotStatus {
    pub running: bool,
    pub active_playlist: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct LogEntry {
    pub timestamp: String,
    pub r#type: String, // "info", "error", "warning", "success"
    pub msg: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RecordStatus {
    pub recording: bool,
    pub live_combo: Option<String>,
    pub has_saved_combo: bool,
}

pub struct ApiClient {
    client: reqwest::Client,
}

impl ApiClient {
    pub fn new() -> Self {
        Self {
            client: reqwest::Client::new(),
        }
    }

    pub async fn get_status(&self) -> Result<GameStatus, reqwest::Error> {
        let url = format!("{}/api/status", BASE_URL);
        self.client.get(&url).send().await?.json::<GameStatus>().await
    }

    pub async fn get_config(&self) -> Result<ConfigResponse, reqwest::Error> {
        let url = format!("{}/api/config", BASE_URL);
        self.client.get(&url).send().await?.json::<ConfigResponse>().await
    }

    pub async fn save_config(&self, settings: &Settings) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/save_config", BASE_URL);
        // Translate front-end style settings names to backend snake_case config names
        let mut body = HashMap::new();
        body.insert("game_process", serde_json::to_value(&settings.gameProcess).unwrap());
        body.insert("game_window", serde_json::to_value(&settings.gameWindow).unwrap());
        body.insert("is_player2_right", serde_json::to_value(settings.isPlayer2Right).unwrap());
        body.insert("delay_frames", serde_json::to_value(settings.delayFrames).unwrap());
        body.insert("start_hotkey", serde_json::to_value(settings.startHotkey.to_lowercase()).unwrap());
        body.insert("stop_hotkey", serde_json::to_value(settings.stopHotkey.to_lowercase()).unwrap());
        body.insert("selected_playlist", serde_json::to_value(&settings.selectedComboSet).unwrap());
        body.insert("hotkeys_enabled", serde_json::to_value(settings.hotkeysEnabled).unwrap());

        let resp = self.client.post(&url).json(&body).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn save_bindings(&self, bindings: &Bindings) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/save_p2_bindings", BASE_URL);
        let mut body = HashMap::new();
        body.insert("bindings", bindings);
        let resp = self.client.post(&url).json(&body).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn get_combos(&self) -> Result<CombosResponse, reqwest::Error> {
        let url = format!("{}/api/combos", BASE_URL);
        self.client.get(&url).send().await?.json::<CombosResponse>().await
    }

    pub async fn create_playlist(&self, name: &str) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/create_playlist", BASE_URL);
        let mut body = HashMap::new();
        body.insert("name", name);
        let resp = self.client.post(&url).json(&body).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn save_combo(&self, combo: &Combo) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/save_combo", BASE_URL);
        let resp = self.client.post(&url).json(combo).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn delete_combo(&self, id: &str) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/delete_combo?id={}", BASE_URL, id);
        let resp = self.client.delete(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn get_bot_status(&self) -> Result<BotStatus, reqwest::Error> {
        let url = format!("{}/api/bot/status", BASE_URL);
        self.client.get(&url).send().await?.json::<BotStatus>().await
    }

    pub async fn start_bot(&self) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/bot/start", BASE_URL);
        let resp = self.client.post(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn stop_bot(&self) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/bot/stop", BASE_URL);
        let resp = self.client.post(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn get_logs(&self) -> Result<Vec<LogEntry>, reqwest::Error> {
        let url = format!("{}/api/logs", BASE_URL);
        self.client.get(&url).send().await?.json::<Vec<LogEntry>>().await
    }

    pub async fn get_record_status(&self) -> Result<RecordStatus, reqwest::Error> {
        let url = format!("{}/api/record/status", BASE_URL);
        self.client.get(&url).send().await?.json::<RecordStatus>().await
    }

    pub async fn start_record(&self) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/record/start", BASE_URL);
        let resp = self.client.post(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn stop_record(&self) -> Result<Option<String>, reqwest::Error> {
        let url = format!("{}/api/record/stop", BASE_URL);
        #[derive(Deserialize)]
        struct StopResp {
            combo: String,
        }
        let resp = self.client.post(&url).send().await?;
        if resp.status().is_success() {
            let data = resp.json::<StopResp>().await?;
            Ok(Some(data.combo))
        } else {
            Ok(None)
        }
    }

    pub async fn cancel_record(&self) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/record/cancel", BASE_URL);
        let resp = self.client.post(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn reset_record(&self) -> Result<bool, reqwest::Error> {
        let url = format!("{}/api/record/reset", BASE_URL);
        let resp = self.client.post(&url).send().await?;
        Ok(resp.status().is_success())
    }

    pub async fn check_alive(&self) -> bool {
        let url = format!("{}/api/status", BASE_URL);
        match self.client.get(&url).send().await {
            Ok(resp) => resp.status().is_success(),
            Err(_) => false,
        }
    }
}
