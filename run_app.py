import os
import sys
import subprocess
import webbrowser
import time
import threading

def main():
    print("=" * 60)
    print("       FIGHTING GAME AUTOMATION ENGINE LAUNCHER         ")
    print("=" * 60)
    
    # 1. Check and install Flask if missing
    try:
        import flask
    except ImportError:
        print("[Loader] Flask package is missing. Installing Flask...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
            print("[Loader] Flask installed successfully.")
        except Exception as e:
            print(f"[Loader Error] Failed to install Flask automatically: {e}")
            print("Please run: pip install flask manually.")
            sys.exit(1)

    # 2. Launch local browser window after server starts
    def open_browser():
        time.sleep(2.0)
        url = "http://127.0.0.1:5000"
        print(f"[Launcher] Opening web app in your browser: {url}")
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    # 3. Start Flask app
    print("[Launcher] Starting Flask API web server on http://127.0.0.1:5000 ...")
    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
