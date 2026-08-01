import os
import sys
import time
import threading

# Add workspace directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, bot_mgr

def start_flask_server():
    """Runs the Flask Web API Server in a daemon thread"""
    # Disable reloader so it doesn't spin up duplicate threads in Flask
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def main():
    print("=" * 60)
    print("       FIGHTING GAME AUTOMATION ENGINE BACKEND          ")
    print("=" * 60)
    print("[Backend] Starting Flask API web server on http://127.0.0.1:5000 ...")
    
    # 1. Run Flask Server in background thread
    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()

    # 2. Wait 1 second for Flask Server to boot
    time.sleep(1.0)
    print("[Backend] Flask server is active. Listening for API requests...")
    
    # Flask app imports hotkeys automatically and registers them on boot.
    # Keep the main thread alive to let daemon threads do their work.
    try:
        while True:
            time.sleep(1.0)
    except (KeyboardInterrupt, SystemExit):
        print("\n[Backend] Shutdown signal received. Cleaning up...")
    finally:
        # Cleanup hotkeys
        if bot_mgr and bot_mgr.hotkey_listener:
            try:
                bot_mgr.hotkey_listener.stop()
                print("[Backend] Unregistered global hotkeys.")
            except Exception as e:
                print(f"[Backend Error] Failed to stop hotkey listener: {e}")
        print("[Backend] Stopped automation engine backend.")

if __name__ == "__main__":
    main()
