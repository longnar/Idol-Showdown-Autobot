import os
import sys
import time
import threading
import webview

# Add workspace directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, bot_mgr

def start_flask_server():
    """Runs the Flask Web API Server in a daemon thread"""
    # Disable reloader so it doesn't spin up duplicate threads in Flask
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def main():
    # 1. Run Flask Server in background thread
    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()

    # 2. Wait 1 second for Flask Server to boot
    time.sleep(1.0)

    # 3. Create PyWebView Window with fixed size 1280x720, resizable=False
    window = webview.create_window(
        title="Idol Showdown Autobot",
        url="http://127.0.0.1:5000",
        width=1280,
        height=720,
        resizable=False
    )

    # 4. Start GUI Loop on Main Thread
    try:
        webview.start(gui="edgechromium")
    finally:
        # Cleanup resources on window closure
        print("[System] Closing application. Disabling hotkey listeners...")
        if bot_mgr and bot_mgr.hotkey_listener:
            try:
                bot_mgr.hotkey_listener.stop()
            except Exception:
                pass
            print("[System] Hotkey listener released successfully.")

if __name__ == "__main__":
    main()
