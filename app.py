import os
import sys
import json
import time
import datetime
import threading
import logging
from flask import Flask, jsonify, request, send_from_directory

# Add workspace directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress Flask/Werkzeug request log spam in TUI mode
if os.environ.get("TUI_MODE") == "1":
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

from config_manager import ConfigManager
from combo_playlist_manager import ComboPlaylistManager, PlaylistOrchestrator
from game_monitor import GameMonitor
from combo_executor import ComboExecutor
from input_mapper import InputMapper
from hotkey import WindowsHotkeyListener
from input_recorder import InputRecorder

# Global Logs Buffer
system_logs = [
    {"timestamp": datetime.datetime.now().strftime("%H:%M:%S"), "type": "info", "msg": "API Server initialization started."}
]

def add_log(log_type: str, msg: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    system_logs.append({
        "timestamp": timestamp,
        "type": log_type,
        "msg": msg
    })
    # Limit to last 100 log entries
    if len(system_logs) > 100:
        system_logs.pop(0)
    if os.environ.get("TUI_MODE") != "1":
        print(f"[{log_type.upper()}] {msg}")

# Stdout Redirector to automatically pipe Python prints into React log panel
class LogRedirector:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        
    def write(self, string):
        if os.environ.get("TUI_MODE") != "1":
            self.original_stdout.write(string)
        msg = string.strip()
        if msg:
            log_type = "info"
            msg_lower = msg.lower()
            if "error" in msg_lower or "lỗi" in msg_lower or "failed" in msg_lower:
                log_type = "error"
            elif "warning" in msg_lower or "cảnh báo" in msg_lower:
                log_type = "warning"
            elif "success" in msg_lower or "ok" in msg_lower or "activated" in msg_lower or "thành công" in msg_lower:
                log_type = "success"
                
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            system_logs.append({
                "timestamp": timestamp,
                "type": log_type,
                "msg": msg
            })
            if len(system_logs) > 100:
                system_logs.pop(0)
                
    def flush(self):
        if os.environ.get("TUI_MODE") != "1":
            self.original_stdout.flush()

# Redirect stdout
sys.stdout = LogRedirector(sys.stdout)

# Initialize Flask app
app = Flask(__name__)

# Initialize Backend Configuration Managers
config_mgr = ConfigManager()
playlist_mgr = ComboPlaylistManager()

# Intermediate database helper for Combos metadata
def load_combos_db():
    if playlist_mgr.first_run:
        combos = []
        with open("combos.json", "w", encoding="utf-8") as f:
            json.dump(combos, f, indent=4)
        playlist_mgr.first_run = False
        return combos

    if not os.path.exists("combos.json"):
        # Import list from playlists.json
        combos = []
        idx = 1
        for pl_name in playlist_mgr.get_playlist_names():
            for input_str in playlist_mgr.get_playlist(pl_name):
                combos.append({
                    "id": str(idx),
                    "name": f"{input_str} (Auto)",
                    "input": input_str,
                    "playlist": pl_name
                })
                idx += 1
        with open("combos.json", "w", encoding="utf-8") as f:
            json.dump(combos, f, indent=4)
        return combos
    else:
        try:
            with open("combos.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

def save_combos_db(combos_list):
    with open("combos.json", "w", encoding="utf-8") as f:
        json.dump(combos_list, f, indent=4)
    
    # Sync playlists.json back
    playlists = {}
    for c in combos_list:
        pl_name = c["playlist"]
        if pl_name not in playlists:
            playlists[pl_name] = []
        playlists[pl_name].append(c["input"])
        
    with open("playlists.json", "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4)

# Global Thread-safe Bot Running State Manager
class BotManager:
    def __init__(self, config_mgr: ConfigManager, playlist_mgr: ComboPlaylistManager):
        self.config_mgr = config_mgr
        self.playlist_mgr = playlist_mgr
        self.orchestrator = None
        self.hotkey_listener = None
        self.running = False
        self.active_playlist = None
        self.main_window = None
        self.overlay_window = None
        self.recorder = InputRecorder()
        self.has_saved_combo = False
        self.saved_combo_str = ""
        self.lock = threading.Lock()
        
    def start_bot(self):
        with self.lock:
            if self.running:
                return
            
            # Reload config to get latest values
            self.config_mgr.config = self.config_mgr.load_config()
            
            # Synchronize and select playlist safely (Fix Lỗi 2)
            playlist_name = self.config_mgr.config.get("selected_playlist", "default")
            playlist_name = self.playlist_mgr.load_and_select_playlist(playlist_name)
            
            # Save the synchronized playlist name back to config.json
            self.config_mgr.config["selected_playlist"] = playlist_name
            self.config_mgr.save_config()
            
            process_name = self.config_mgr.config.get("game_process", "")
            window_title = self.config_mgr.config.get("game_window", "")
            
            # Launch modules
            game_monitor = GameMonitor(self.config_mgr)
            executor = ComboExecutor(self.config_mgr, game_monitor, 60.0)
            mapper = InputMapper(self.config_mgr)
            
            self.orchestrator = PlaylistOrchestrator(
                playlist_name=playlist_name,
                playlist_manager=self.playlist_mgr,
                executor=executor,
                mapper=mapper,
                game_monitor=game_monitor,
                fps=60.0
            )
            
            self.orchestrator.start()
            self.running = True
            self.active_playlist = playlist_name
            add_log("success", f"Bot playlist loop started for '{playlist_name.upper()}'.")
            
    def stop_bot(self):
        with self.lock:
            if not self.running:
                return
            if self.orchestrator:
                self.orchestrator.stop()
                self.orchestrator = None
            self.running = False
            self.active_playlist = None
            add_log("warning", "Bot playlist loop stopped.")
            
    def toggle_bot(self, action: str):
        print(f"[Debug Hotkey] toggle_bot called with action: '{action}'")
        if action == "start":
            self.start_bot()
        elif action == "stop":
            self.stop_bot()
            
    def setup_hotkeys(self):
        # Stop current listener
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None
            
        if self.config_mgr.config.get("hotkeys_enabled", True):
            start_hk = self.config_mgr.config.get("start_hotkey", "f9").lower()
            stop_hk = self.config_mgr.config.get("stop_hotkey", "f10").lower()
            
            self.hotkey_listener = WindowsHotkeyListener()
            try:
                self.hotkey_listener.register_hotkey(start_hk, lambda: self.toggle_bot("start"))
                self.hotkey_listener.register_hotkey(stop_hk, lambda: self.toggle_bot("stop"))
                self.hotkey_listener.start()
                add_log("success", f"Registered global hotkeys: START={start_hk.upper()}, STOP={stop_hk.upper()}")
            except Exception as e:
                add_log("error", f"Could not bind global hotkeys: {e}")
        else:
            add_log("warning", "Global hotkeys are disabled (Turned OFF in configuration).")

bot_mgr = BotManager(config_mgr, playlist_mgr)

@app.before_request
def update_interaction_time():
    # If the endpoint is NOT static or polling state/logs, update interaction time
    path = request.path
    if not path.startswith("/static") and path not in ("/api/status", "/api/logs", "/api/bot/status", "/"):
        GameMonitor.update_interaction()

# ----------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------

# Root route status
@app.route("/")
def index():
    return jsonify({"status": "active", "message": "Idol Showdown Autobot Backend API"})

@app.route("/api/status", methods=["GET"])
def get_status():
    process_name = config_mgr.config.get("game_process", "")
    window_title = config_mgr.config.get("game_window", "")
    game_monitor = GameMonitor(config_mgr)
    return jsonify({
        "game_running": game_monitor.is_game_running(),
        "game_focused": game_monitor.is_game_focused(),
        "game_process": process_name,
        "game_window": window_title,
        "game_pid": game_monitor.get_game_pid()
    })

@app.route("/api/config", methods=["GET"])
def get_config():
    config_mgr.config = config_mgr.load_config()
    conf = config_mgr.config
    
    settings = {
        "gameStatus": "Active" if bot_mgr.running else "Stopped",
        "delayFrames": conf.get("delay_frames", 30),
        "isPlayer2Right": conf.get("is_player2_right", True),
        "selectedComboSet": conf.get("selected_playlist", "test_1"),
        "startHotkey": conf.get("start_hotkey", "F9").upper(),
        "stopHotkey": conf.get("stop_hotkey", "F10").upper(),
        "gameProcess": conf.get("game_process", ""),
        "gameWindow": conf.get("game_window", ""),
        "hotkeysEnabled": conf.get("hotkeys_enabled", True)
    }
    
    # Map backend binding keys to frontend names
    b = conf.get("bindings", {})
    bindings = {
        "Jump": b.get("Up", "w"),
        "Crouch": b.get("Down", "s"),
        "Left": b.get("Left", "a"),
        "Right": b.get("Right", "d"),
        "Light": b.get("Light", "j"),
        "Medium": b.get("Medium", "k"),
        "Heavy": b.get("Heavy", "l"),
        "Special": b.get("Special", "i"),
        "Burst": b.get("Burst", "u"),
        "Collab": b.get("Collab", "o"),
        "Items": b.get("Items", "h"),
        "Grab": b.get("Grab", "g")
    }
    
    return jsonify({
        "settings": settings,
        "bindings": bindings
    })

@app.route("/api/save_config", methods=["POST"])
def save_config():
    data = request.json
    
    config_mgr.config["game_process"] = data.get("game_process", config_mgr.config.get("game_process"))
    config_mgr.config["game_window"] = data.get("game_window", config_mgr.config.get("game_window"))
    config_mgr.config["is_player2_right"] = data.get("is_player2_right", True)
    config_mgr.config["delay_frames"] = int(data.get("delay_frames", 30))
    config_mgr.config["start_hotkey"] = data.get("start_hotkey", "f9").lower()
    config_mgr.config["stop_hotkey"] = data.get("stop_hotkey", "f10").lower()
    config_mgr.config["selected_playlist"] = data.get("selected_playlist", "test_1")
    config_mgr.config["hotkeys_enabled"] = data.get("hotkeys_enabled", True)
    
    config_mgr.save_config()
    bot_mgr.setup_hotkeys()
    
    add_log("success", "Saved general settings configurations.")
    return jsonify({"success": True})

@app.route("/api/save_p2_bindings", methods=["POST"])
def save_p2_bindings():
    data = request.json
    bindings_req = data.get("bindings", {})
    
    from direct_input import SCAN_CODES
    
    # Map React keys back to Python keys
    python_bindings = {
        "Up": bindings_req.get("Up", "w").lower(),
        "Down": bindings_req.get("Down", "s").lower(),
        "Left": bindings_req.get("Left", "a").lower(),
        "Right": bindings_req.get("Right", "d").lower(),
        "Light": bindings_req.get("Light", "j").lower(),
        "Medium": bindings_req.get("Medium", "k").lower(),
        "Heavy": bindings_req.get("Heavy", "l").lower(),
        "Special": bindings_req.get("Special", "i").lower(),
        "Burst": bindings_req.get("Burst", "u").lower(),
        "Collab": bindings_req.get("Collab", "o").lower(),
        "Items": bindings_req.get("Items", "h").lower(),
        "Grab": bindings_req.get("Grab", "g").lower()
    }
    
    # Validate keys
    for act, key in python_bindings.items():
        if key not in SCAN_CODES:
            add_log("error", f"Binding error: '{key}' is not mapped in direct_input scan codes.")
            return jsonify({"success": False, "message": f"Phím '{key.upper()}' không được hỗ trợ."}), 400
            
    config_mgr.config["bindings"] = python_bindings
    config_mgr.save_config()
    add_log("success", "Synchronized 12 Player 2 virtual key bindings.")
    return jsonify({"success": True})


@app.route("/api/playlists", methods=["GET"])
def get_playlists():
    playlist_mgr.playlists = playlist_mgr.load_playlists()
    return jsonify(playlist_mgr.get_playlist_names())

@app.route("/api/combos", methods=["GET"])
def get_combos():
    combos_list = load_combos_db()
    playlist_mgr.playlists = playlist_mgr.load_playlists()
    return jsonify({
        "combos": combos_list,
        "playlists": playlist_mgr.get_playlist_names()
    })

@app.route("/api/create_playlist", methods=["POST"])
def create_playlist():
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Tên danh sách không được để trống"}), 400
        
    playlist_mgr.playlists = playlist_mgr.load_playlists()
    if name in playlist_mgr.playlists:
        return jsonify({"success": False, "message": "Tên danh sách đã tồn tại"}), 400
        
    playlist_mgr.create_playlist(name)
    playlist_mgr.reload_playlists()
    add_log("success", f"Created new playlist '{name}'.")
    return jsonify({"success": True})

@app.route("/api/save_combo", methods=["POST"])
def save_combo():
    data = request.json
    name = data.get("name", "").strip()
    combo_input = data.get("input", "").strip()
    playlist = data.get("playlist", "").strip()
    combo_id = data.get("id")
    
    if not name or not combo_input or not playlist:
        return jsonify({"success": False, "message": "Thông tin đầu vào không đầy đủ"}), 400
        
    is_numpad = any(char.isdigit() for char in combo_input)
    try:
        from input_mapper import InputMapper
        mapper = InputMapper(config_mgr)
        mapper.parse_combo(combo_input, is_numpad=is_numpad)
    except ValueError as ve:
        add_log("error", f"Invalid combo syntax: {ve}")
        return jsonify({"success": False, "message": f"Sai cú pháp combo: {ve}"}), 400
        
    combos_list = load_combos_db()
    if combo_id:
        # Edit mode
        found = False
        for c in combos_list:
            if c["id"] == str(combo_id):
                c["name"] = name
                c["input"] = combo_input
                c["playlist"] = playlist
                found = True
                break
        if not found:
            return jsonify({"success": False, "message": "Không tìm thấy combo"}), 404
        add_log("success", f"Updated combo '{name}' ({combo_input}) in playlist '{playlist}'.")
    else:
        # Create mode
        new_id = str(int(time.time() * 1000))
        combos_list.append({
            "id": new_id,
            "name": name,
            "input": combo_input,
            "playlist": playlist
        })
        add_log("success", f"Created combo '{name}' ({combo_input}) in playlist '{playlist}'.")
        
    save_combos_db(combos_list)
    playlist_mgr.playlists = playlist_mgr.load_playlists()
    
    return jsonify({"success": True})

@app.route("/api/delete_combo", methods=["DELETE"])
def delete_combo():
    combo_id = request.args.get("id")
    if not combo_id:
        return jsonify({"success": False, "message": "Thiếu combo id"}), 400
        
    combos_list = load_combos_db()
    found_combo = None
    for c in combos_list:
        if c["id"] == str(combo_id):
            found_combo = c
            break
            
    if found_combo:
        combos_list.remove(found_combo)
        save_combos_db(combos_list)
        playlist_mgr.playlists = playlist_mgr.load_playlists()
        add_log("warning", f"Removed combo '{found_combo['name']}' from database.")
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Không tìm thấy combo"}), 404

@app.route("/api/test_combo", methods=["POST"])
def api_test_combo():
    data = request.json
    combo_sequence = data.get("combo_sequence", "").strip()
    is_numpad = data.get("is_numpad", True)
    
    if not combo_sequence:
        return jsonify({"success": False, "notice": "[LỖI] Chuỗi combo rỗng!"}), 400
        
    config_mgr.config = config_mgr.load_config()
    process_name = config_mgr.config.get("game_process", "")
    window_title = config_mgr.config.get("game_window", "")
    game_monitor = GameMonitor(config_mgr)
    
    if not game_monitor.is_game_running():
        msg = f"[LỖI] Tiến trình game '{process_name}' không hoạt động!"
        add_log("error", msg)
        return jsonify({"success": False, "notice": msg})
        
    result = {"success": False, "notice": ""}
    event = threading.Event()
    
    def run_test_thread():
        add_log("info", "Hãy kích hoạt/nhấp chuột chọn cửa sổ game trong vòng 3 giây để thực thi thử nghiệm...")
        time.sleep(3.0)
        
        if not game_monitor.check_fail_safe():
            msg = "[Test Failed] Game không được focus hoặc không hoạt động!"
            add_log("error", msg)
            result["success"] = False
            result["notice"] = msg
            event.set()
            return
            
        executor = ComboExecutor(config_mgr, game_monitor, 60.0)
        mapper = InputMapper(config_mgr)
        try:
            key_events = mapper.parse_combo(combo_sequence, is_numpad=is_numpad)
            if key_events:
                add_log("info", f"[Test Bot] Bắt đầu thi triển: '{combo_sequence}'")
                exec_success = executor.execute_overlapping_combo(key_events)
                if exec_success:
                    msg = f"[TEST OK] Thi triển hoàn tất combo: '{combo_sequence}'"
                    if mapper.j_analysis_logs:
                        msg += "\n" + "\n".join(mapper.j_analysis_logs)
                    add_log("success", msg)
                    result["success"] = True
                    result["notice"] = msg
                else:
                    msg = f"[LỖI] Không thể thi triển combo: '{combo_sequence}'"
                    add_log("error", msg)
                    result["success"] = False
                    result["notice"] = msg
            else:
                msg = f"[LỖI] Cú pháp combo không thể giải mã: '{combo_sequence}'"
                add_log("error", msg)
                result["success"] = False
                result["notice"] = msg
        except ValueError as ve:
            msg = f"[LỖI CÚ PHÁP] {ve}"
            add_log("error", msg)
            result["success"] = False
            result["notice"] = msg
        except Exception as e:
            msg = f"[LỖI] Ngoại lệ khi thi triển combo: {e}"
            add_log("error", msg)
            result["success"] = False
            result["notice"] = msg
        event.set()
        
    threading.Thread(target=run_test_thread, daemon=True).start()
    
    # Wait for the thread to complete (up to 15 seconds)
    completed = event.wait(timeout=15.0)
    if not completed:
        msg = "[LỖI] Quá thời gian chờ kiểm thử (Timeout 15s)!"
        add_log("error", msg)
        return jsonify({
            "success": False,
            "notice": msg
        })
        
    return jsonify(result)

@app.route("/api/select_combo", methods=["POST"])
def api_select_combo():
    data = request.json
    combo_input = data.get("input", "")
    combo_name = data.get("name", "")
    
    if not combo_input:
        return jsonify({"success": False}), 400
        
    config_mgr.config = config_mgr.load_config()
    process_name = config_mgr.config.get("game_process", "")
    window_title = config_mgr.config.get("game_window", "")
    game_monitor = GameMonitor(config_mgr)
    
    if not game_monitor.is_game_running():
        add_log("error", f"Lỗi thi triển nhanh: Game '{process_name}' không chạy.")
        return jsonify({"success": False}), 400
        
    def run_select_thread():
        add_log("info", f"Thi triển nhanh đòn đánh '{combo_name}' trong 1 giây...")
        time.sleep(1.0)
        if not game_monitor.check_fail_safe():
            add_log("error", f"Thi triển '{combo_name}' thất bại: Cửa sổ game không được focus!")
            return
        executor = ComboExecutor(config_mgr, game_monitor, 60.0)
        mapper = InputMapper(config_mgr)
        try:
            is_numpad = any(char.isdigit() for char in combo_input)
            key_events = mapper.parse_combo(combo_input, is_numpad=is_numpad)
            if key_events:
                executor.execute_overlapping_combo(key_events)
            else:
                add_log("error", f"Lỗi parse combo: {combo_input}")
        except Exception as e:
            add_log("error", f"Lỗi thi triển nhanh đòn: {e}")
            
    threading.Thread(target=run_select_thread, daemon=True).start()
    return jsonify({"success": True})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(system_logs)

@app.route("/api/bot/status", methods=["GET"])
def get_bot_status():
    if bot_mgr.orchestrator:
        if not bot_mgr.orchestrator.is_running and bot_mgr.running:
            bot_mgr.running = False
            bot_mgr.active_playlist = None
    return jsonify({
        "running": bot_mgr.running,
        "active_playlist": bot_mgr.active_playlist
    })

@app.route("/api/bot/start", methods=["POST"])
def api_start_bot():
    bot_mgr.start_bot()
    return jsonify({"success": True})

@app.route("/api/bot/stop", methods=["POST"])
def api_stop_bot():
    bot_mgr.stop_bot()
    return jsonify({"success": True})

# Setup hotkeys on startup
bot_mgr.setup_hotkeys()

@app.route("/overlay")
def render_overlay():
    html_content = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Idol Showdown Overlay</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #030712;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100vw;
      height: 100vh;
      -webkit-app-region: drag;
    }
    .overlay-container {
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 15px;
      box-sizing: border-box;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(3, 7, 18, 0.95));
      border: 1.5px solid #06b6d4;
      box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
    }
    .left-controls, .right-controls {
      display: flex;
      align-items: center;
      gap: 8px;
      -webkit-app-region: no-drag;
    }
    button {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      width: 28px;
      height: 28px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      transition: all 0.2s;
    }
    button:hover {
      background: #334155;
      border-color: #475569;
      color: #f1f5f9;
      box-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
    }
    button.save-btn {
      background: rgba(6, 182, 212, 0.1);
      border-color: rgba(6, 182, 212, 0.3);
      color: #06b6d4;
      width: 65px;
      font-weight: bold;
      font-size: 10px;
    }
    button.save-btn:hover {
      background: #06b6d4;
      border-color: #22d3ee;
      color: #090d16;
      box-shadow: 0 0 10px rgba(6, 182, 212, 0.4);
    }
    .feedback-display {
      flex: 1;
      margin: 0 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(0, 0, 0, 0.4);
      padding: 6px 12px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      height: 20px;
      overflow: hidden;
    }
    .rec-dot {
      width: 7px;
      height: 7px;
      background-color: #ef4444;
      border-radius: 50%;
      animation: pulse 1s infinite alternate;
      flex-shrink: 0;
    }
    #combo-text {
      font-family: Consolas, Monaco, monospace;
      font-size: 11px;
      color: #22d3ee;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
      font-weight: bold;
      text-shadow: 0 0 5px rgba(34, 211, 238, 0.3);
    }
    @keyframes pulse {
      from { opacity: 0.3; transform: scale(0.9); }
      to { opacity: 1; transform: scale(1.1); }
    }
  </style>
</head>
<body>
  <div class="overlay-container">
    <div class="left-controls">
      <button onclick="resetRecord()" title="Làm mới (Reset)">⟳</button>
      <button onclick="cancelRecord()" title="Hủy bỏ (Cancel)">✕</button>
      <button onclick="testRecord()" title="Chạy thử (Play)">▶</button>
    </div>
    
    <div class="feedback-display">
      <div class="rec-dot"></div>
      <div id="combo-text">Đang lắng nghe...</div>
    </div>
    
    <div class="right-controls">
      <button onclick="saveRecord()" class="save-btn" title="Lưu lại (Save)">💾 LƯU</button>
    </div>
  </div>

  <script>
    function updateLiveCombo() {
      fetch('/api/record/status')
        .then(res => res.json())
        .then(data => {
          const comboText = document.getElementById('combo-text');
          if (data.live_combo) {
            comboText.textContent = data.live_combo;
          } else {
            comboText.textContent = 'Hãy gõ phím di chuyển / đòn đánh...';
          }
        })
        .catch(err => console.error(err));
    }

    setInterval(updateLiveCombo, 100);

    function resetRecord() {
      fetch('/api/record/reset', { method: 'POST' });
    }

    function cancelRecord() {
      fetch('/api/record/cancel', { method: 'POST' });
    }

    function saveRecord() {
      fetch('/api/record/stop', { method: 'POST' });
    }

    function testRecord() {
      fetch('/api/record/test', { method: 'POST' });
    }
  </script>
</body>
</html>"""
    return html_content

@app.route("/api/record/start", methods=["POST"])
def start_record():
    bot_mgr.recorder.start()
    bot_mgr.has_saved_combo = False
    bot_mgr.saved_combo_str = ""
    
    if bot_mgr.main_window:
        try:
            bot_mgr.main_window.minimize()
        except Exception as e:
            print(f"[Overlay Debug] Error minimizing main window: {e}")
            
    if bot_mgr.overlay_window:
        try:
            bot_mgr.overlay_window.show()
        except Exception as e:
            print(f"[Overlay Debug] Error showing overlay window: {e}")
            
    add_log("info", "Bắt đầu ghi phím. Giao diện chính đã thu nhỏ.")
    return jsonify({"success": True})

@app.route("/api/record/stop", methods=["POST"])
def stop_record():
    combo = bot_mgr.recorder.stop()
    bot_mgr.saved_combo_str = combo
    bot_mgr.has_saved_combo = True
    
    if bot_mgr.overlay_window:
        try:
            bot_mgr.overlay_window.hide()
        except Exception as e:
            print(f"[Overlay Debug] Error hiding overlay window: {e}")
            
    if bot_mgr.main_window:
        try:
            bot_mgr.main_window.restore()
        except Exception as e:
            print(f"[Overlay Debug] Error restoring main window: {e}")
            
    add_log("success", f"Đã lưu combo ghi được: '{combo}'")
    return jsonify({"success": True, "combo": combo})

@app.route("/api/record/cancel", methods=["POST"])
def cancel_record():
    bot_mgr.recorder.stop()
    bot_mgr.has_saved_combo = False
    bot_mgr.saved_combo_str = ""
    
    if bot_mgr.overlay_window:
        try:
            bot_mgr.overlay_window.hide()
        except Exception as e:
            print(f"[Overlay Debug] Error hiding overlay window: {e}")
            
    if bot_mgr.main_window:
        try:
            bot_mgr.main_window.restore()
        except Exception as e:
            print(f"[Overlay Debug] Error restoring main window: {e}")
            
    add_log("warning", "Đã hủy quá trình ghi phím.")
    return jsonify({"success": True})

@app.route("/api/record/reset", methods=["POST"])
def reset_record():
    bot_mgr.recorder.reset()
    return jsonify({"success": True})

@app.route("/api/record/status", methods=["GET"])
def get_record_status():
    return jsonify({
        "recording": bot_mgr.recorder.is_recording,
        "live_combo": bot_mgr.recorder.live_combo_string,
        "has_saved_combo": bot_mgr.has_saved_combo
    })

@app.route("/api/record/saved_combo", methods=["GET"])
def get_saved_combo():
    combo = bot_mgr.saved_combo_str
    bot_mgr.has_saved_combo = False
    bot_mgr.saved_combo_str = ""
    return jsonify({"combo": combo})

@app.route("/api/record/test", methods=["POST"])
def test_recorded_combo():
    combo = bot_mgr.recorder.live_combo_string
    if not combo:
        return jsonify({"success": False, "message": "Không có combo nào để chạy thử"}), 400
        
    config_mgr.config = config_mgr.load_config()
    process_name = config_mgr.config.get("game_process", "")
    window_title = config_mgr.config.get("game_window", "")
    game_monitor = GameMonitor(config_mgr)
    
    if not game_monitor.is_game_running():
        add_log("error", f"Chạy thử thất bại: Game '{process_name}' không hoạt động.")
        return jsonify({"success": False, "message": "Game không chạy"}), 400
        
    def run_test():
        add_log("info", "Bắt đầu chạy thử combo vừa ghi trong 1 giây...")
        time.sleep(1.0)
        if not game_monitor.check_fail_safe():
            add_log("error", "Chạy thử thất bại: Không thể focus cửa sổ game!")
            return
        executor = ComboExecutor(config_mgr, game_monitor, 60.0)
        mapper = InputMapper(config_mgr)
        try:
            key_events = mapper.parse_combo(combo, is_numpad=True)
            if key_events:
                executor.execute_overlapping_combo(key_events)
            else:
                add_log("error", f"Không thể giải mã combo: {combo}")
        except Exception as e:
            add_log("error", f"Ngoại lệ chạy thử: {e}")
            
    threading.Thread(target=run_test, daemon=True).start()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
