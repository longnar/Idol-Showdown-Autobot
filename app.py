import os
import sys
import json
import time
import datetime
import threading
from flask import Flask, jsonify, request, send_from_directory

# Add workspace directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from combo_playlist_manager import ComboPlaylistManager, PlaylistOrchestrator
from game_monitor import GameMonitor
from combo_executor import ComboExecutor
from input_mapper import InputMapper
from hotkey import WindowsHotkeyListener

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
    print(f"[{log_type.upper()}] {msg}")

# Stdout Redirector to automatically pipe Python prints into React log panel
class LogRedirector:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        
    def write(self, string):
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
        self.original_stdout.flush()

# Redirect stdout
sys.stdout = LogRedirector(sys.stdout)

# Initialize Flask app
# Static folder set to gui/dist to serve React static bundle in production
if getattr(sys, 'frozen', False):
    static_folder = os.path.join(sys._MEIPASS, "gui", "dist")
else:
    static_folder = "gui/dist"

app = Flask(__name__, static_folder=static_folder, static_url_path="")

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

# Serve React static assets
@app.route("/")
def index():
    return app.send_static_file("index.html")

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
        "gameWindow": conf.get("game_window", "")
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
