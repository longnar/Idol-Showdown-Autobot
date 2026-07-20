import ctypes
import time

# Windows Constants
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Define ULONG_PTR based on OS architecture (32-bit vs 64-bit)
ULONG_PTR = ctypes.c_size_t

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]

# Keyboard Scan Codes (PS/2 Set 1)
# Standard keys are normal keys; Arrow keys and some others are extended.
SCAN_CODES = {
    # Letters
    'a': (0x1E, False), 'b': (0x30, False), 'c': (0x2E, False), 'd': (0x20, False),
    'e': (0x12, False), 'f': (0x21, False), 'g': (0x22, False), 'h': (0x23, False),
    'i': (0x17, False), 'j': (0x24, False), 'k': (0x25, False), 'l': (0x26, False),
    'm': (0x32, False), 'n': (0x31, False), 'o': (0x18, False), 'p': (0x19, False),
    'q': (0x10, False), 'r': (0x13, False), 's': (0x1F, False), 't': (0x14, False),
    'u': (0x16, False), 'v': (0x2F, False), 'w': (0x11, False), 'x': (0x2D, False),
    'y': (0x15, False), 'z': (0x2C, False),
    
    # Numbers (top row)
    '1': (0x02, False), '2': (0x03, False), '3': (0x04, False), '4': (0x05, False),
    '5': (0x06, False), '6': (0x07, False), '7': (0x08, False), '8': (0x09, False),
    '9': (0x0A, False), '0': (0x0B, False),

    # Controls & Navigation
    'space': (0x39, False),
    'enter': (0x1C, False),
    'esc': (0x01, False),
    'backspace': (0x0E, False),
    'tab': (0x0F, False),
    'shift': (0x2A, False),       # Left shift
    'ctrl': (0x1D, False),        # Left control
    'alt': (0x38, False),         # Left alt
    
    # Arrow Keys (Extended)
    'up': (0x48, True),
    'down': (0x50, True),
    'left': (0x4B, True),
    'right': (0x4D, True),
    
    # Numpad (P2 standard layout is often numpad)
    'num_1': (0x4F, False), 'num_2': (0x50, False), 'num_3': (0x51, False),
    'num_4': (0x4B, False), 'num_5': (0x4C, False), 'num_6': (0x4D, False),
    'num_7': (0x47, False), 'num_8': (0x48, False), 'num_9': (0x49, False),
    'num_0': (0x52, False),
}

def get_movement_keys_mapping():
    """
    Loads active bindings from config.json if available.
    Returns a dictionary mapping '1'-'9' to lists of physical keys.
    """
    import json
    import os
    
    # Default fallback bindings
    bindings = {
        "Up": "w",
        "Down": "s",
        "Left": "a",
        "Right": "d"
    }
    
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "bindings" in config:
                    b = config["bindings"]
                    for action in ["Up", "Down", "Left", "Right"]:
                        if action in b:
                            bindings[action] = b[action]
        except Exception:
            pass
            
    numpad_map = {
        '1': [bindings["Down"], bindings["Left"]],
        '2': [bindings["Down"]],
        '3': [bindings["Down"], bindings["Right"]],
        '4': [bindings["Left"]],
        '5': [],
        '6': [bindings["Right"]],
        '7': [bindings["Up"], bindings["Left"]],
        '8': [bindings["Up"]],
        '9': [bindings["Up"], bindings["Right"]]
    }
    return numpad_map

def press_key(key_name: str):
    """Presses a key and holds it (until released). Supports numpad notations (1-9)."""
    key_name = str(key_name).lower()
    
    # Check if key is a numpad notation 1-9
    if key_name in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
        numpad_map = get_movement_keys_mapping()
        mapped_keys = numpad_map[key_name]
        success = True
        for mk in mapped_keys:
            if not press_key(mk):
                success = False
        return success

    if key_name not in SCAN_CODES:
        print(f"[Warning] Unknown key: {key_name}")
        return False
        
    scan_code, is_extended = SCAN_CODES[key_name]
    
    flags = KEYEVENTF_SCANCODE
    if is_extended:
        flags |= KEYEVENTF_EXTENDEDKEY
        
    ki = KEYBDINPUT(0, scan_code, flags, 0, 0)
    union = INPUT_UNION(ki=ki)
    input_struct = INPUT(type=INPUT_KEYBOARD, union=union)
    
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
    return True

def release_key(key_name: str):
    """Releases a key. Supports numpad notations (1-9)."""
    key_name = str(key_name).lower()
    
    # Check if key is a numpad notation 1-9
    if key_name in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
        numpad_map = get_movement_keys_mapping()
        mapped_keys = numpad_map[key_name]
        success = True
        for mk in mapped_keys:
            if not release_key(mk):
                success = False
        return success

    if key_name not in SCAN_CODES:
        return False
        
    scan_code, is_extended = SCAN_CODES[key_name]
    
    flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
    if is_extended:
        flags |= KEYEVENTF_EXTENDEDKEY
        
    ki = KEYBDINPUT(0, scan_code, flags, 0, 0)
    union = INPUT_UNION(ki=ki)
    input_struct = INPUT(type=INPUT_KEYBOARD, union=union)
    
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
    return True

def press_and_release(key_name: str, duration_sec: float = 0.05):
    """Presses and releases a key with a small delay."""
    if press_key(key_name):
        time.sleep(duration_sec)
        release_key(key_name)
