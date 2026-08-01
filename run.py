import os
import sys
import time
import threading
import subprocess

# Set TUI mode before importing app so it knows not to print to console
os.environ["TUI_MODE"] = "1"

# Add workspace directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, bot_mgr

def start_flask_server():
    """Runs the Flask Web API Server in a daemon thread"""
    # Disable reloader so it doesn't spin up duplicate threads in Flask
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def find_cargo_executable():
    """Tries to find cargo.exe in common locations and system PATH"""
    # 1. Check if cargo is available in system PATH
    try:
        subprocess.run(["cargo", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "cargo"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # 2. Check custom D:\Rust path and default user profiles
    custom_paths = [
        r"D:\Rust\cargo\bin\cargo.exe",
        r"D:\Rust\bin\cargo.exe",
        os.path.expandvars(r"%USERPROFILE%\.cargo\bin\cargo.exe"),
    ]

    for path in custom_paths:
        if os.path.exists(path):
            return path

    return None

def check_cargo_available(cargo_cmd):
    """Checks if the resolved cargo command is executable"""
    if not cargo_cmd:
        return False
    try:
        subprocess.run([cargo_cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def build_rust_tui(cargo_cmd):
    """Tries to compile the Rust TUI client using the resolved cargo command"""
    print(f"[Launcher] Dang bien dich Rust Ratatui TUI client dung: {cargo_cmd}")
    manifest_path = os.path.join("gui_tui", "Cargo.toml")
    try:
        # We need to add D:\Rust\cargo\bin to PATH temporarily during compilation
        # so cargo.exe can find rustc.exe in the same toolchain directory.
        env = os.environ.copy()
        cargo_dir = os.path.dirname(cargo_cmd)
        if cargo_dir:
            env["PATH"] = cargo_dir + os.pathsep + env.get("PATH", "")

        # Use -j 1 to avoid Windows file locks conflicts during parallel compilation
        result = subprocess.run([cargo_cmd, "build", "-j", "1", "--release", "--manifest-path", manifest_path], env=env, check=True)
        return result.returncode == 0
    except Exception as e:
        print(f"[Launcher Error] Khong the bien dich TUI: {e}")
        return False

def main():
    print("=" * 60)
    print("         IDOL SHOWDOWN AUTOBOT LAUNCHER (TUI)           ")
    print("=" * 60)

    # 1. Resolve cargo command location
    cargo_cmd = find_cargo_executable()

    # 2. Locate Rust TUI Binary
    tui_exe = None
    if getattr(sys, 'frozen', False):
        tui_exe = os.path.join(sys._MEIPASS, "gui_tui.exe")
    else:
        binary_release = os.path.join("gui_tui", "target", "release", "gui_tui.exe")
        binary_debug = os.path.join("gui_tui", "target", "debug", "gui_tui.exe")
        if os.path.exists(binary_release):
            tui_exe = binary_release
        elif os.path.exists(binary_debug):
            tui_exe = binary_debug
        else:
            # Binary not found, try compiling it
            if cargo_cmd and check_cargo_available(cargo_cmd):
                if build_rust_tui(cargo_cmd) and os.path.exists(binary_release):
                    tui_exe = binary_release
            else:
                print("\n[Luu y] Khong tim thay file thuc thi TUI va may chua cai dat Rust Compiler (Cargo).")
                print("De chay ung dung voi giao dien Ratatui TUI moi, vui long cai dat Rust:")
                print("  Chay lenh sau trong PowerShell (Admin):")
                print("  Invoke-WebRequest -Uri \"https://win.rustup.rs/x86_64\" -OutFile \"rustup-init.exe\"; .\\rustup-init.exe -y")
                print("\nSau khi cai dat Rust, hay tat va mo lai terminal roi chay lai 'python run.py'.")
                input("\nNhan Enter de thoat...")
                sys.exit(1)

    if not tui_exe:
        print("[Loi] Khong the tim thay hoac bien dich file thuc thi TUI tai 'gui_tui/target/release/gui_tui.exe'.")
        input("\nNhan Enter de thoat...")
        sys.exit(1)

    # 3. Run Flask API Server in background thread
    print("[Launcher] Dang khoi dong automation backend engine...")
    
    # Save original stdout/stderr references and redirect to debug_run.txt
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    
    debug_log = open("debug_run.txt", "w", encoding="utf-8")
    sys.stdout = debug_log
    sys.stderr = debug_log

    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()

    # Wait for backend to fully initialize
    time.sleep(1.5)
    orig_stdout.write("[Launcher] Backend active. Dang chay TUI frontend...\n")
    orig_stdout.flush()

    # 4. Launch Rust TUI client in foreground (inheriting stdin/stdout/stderr)
    try:
        # Add cargo bin path to process environment so the Rust TUI process can call cargo if it ever needs to,
        # but more importantly, to keep environment consistent.
        env = os.environ.copy()
        if cargo_cmd and cargo_cmd != "cargo":
            env["PATH"] = os.path.dirname(cargo_cmd) + os.pathsep + env.get("PATH", "")

        subprocess.run([tui_exe], env=env, check=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[Launcher Error] TUI bi crash hoac dong dot ngot: {e}")
    finally:
        # 5. Cleanup resources on exit
        print("\n[Launcher] Dang dung ung dung. Releasing hotkey listeners...")
        if bot_mgr and bot_mgr.hotkey_listener:
            try:
                bot_mgr.hotkey_listener.stop()
            except Exception:
                pass
            print("[Launcher] Hotkey listener released successfully.")
        print("[Launcher] Shutdown complete. Goodbye!")

if __name__ == "__main__":
    main()
