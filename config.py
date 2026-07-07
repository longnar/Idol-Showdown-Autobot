from sequence import InputStep, InputSequence

# ---------------------------------------------------------
# TARGET GAME CONFIGURATION
# ---------------------------------------------------------
# Target window title (substring match, case-insensitive).
# For easy initial verification, we default to "Notepad".
# Change this to your game title (e.g., "Street Fighter V", "Tekken 8", "Guilty Gear").
TARGET_GAME_WINDOW = "Notepad"

# Game speed in frames per second
FPS = 60.0

# ---------------------------------------------------------
# HOTKEYS CONFIGURATION
# ---------------------------------------------------------
# System-wide global hotkeys to control the bot.
HOTKEY_START = "f9"
HOTKEY_STOP = "f10"

# ---------------------------------------------------------
# TIMING CONFIGURATION
# ---------------------------------------------------------
# Delay range between executing sequences (in frames).
# 30 to 60 frames translates to 0.5s to 1.0s at 60 FPS.
DELAY_MIN_FRAMES = 30
DELAY_MAX_FRAMES = 60

# If True, randomly picks from the SEQUENCES list.
# If False, loops through them sequentially.
RANDOM_MODE = True

# ---------------------------------------------------------
# INPUT SEQUENCES FOR PLAYER 2
# ---------------------------------------------------------
# Player 2 Movement Keys: 'up', 'down', 'left', 'right' (Arrow keys)
# Player 2 Attack Keys: 'num_1' (Light Punch), 'num_2' (Medium Punch), 'num_3' (Heavy Punch),
#                       'num_4' (Light Kick), 'num_5' (Medium Kick), 'num_6' (Heavy Kick)

# 1. Hadouken / Fireball (QCF + Punch) for P2 facing Left (Down -> Down-Left -> Left + Punch)
hadouken_p2 = InputSequence(
    name="Hadouken (Facing Left)",
    steps=[
        InputStep(keys="down", duration_frames=3),
        InputStep(keys=["down", "left"], duration_frames=3),
        InputStep(keys="left", duration_frames=3),
        InputStep(keys=["left", "num_1"], duration_frames=4),
    ]
)

# 2. Shoryuken / Dragon Punch (SRK) for P2 facing Left (Left -> Down -> Down-Left + Punch)
shoryuken_p2 = InputSequence(
    name="Shoryuken (Facing Left)",
    steps=[
        InputStep(keys="left", duration_frames=3),
        InputStep(keys="down", duration_frames=3),
        InputStep(keys=["down", "left"], duration_frames=3),
        InputStep(keys=["down", "left", "num_2"], duration_frames=4),
    ]
)

# 3. Simple Poke: Light Kick
light_kick_p2 = InputSequence(
    name="Light Kick Poke",
    steps=[
        InputStep(keys="num_4", duration_frames=4)
    ]
)

# 4. Jump Back Kick (Up-Right -> Heavy Kick)
jump_back_kick_p2 = InputSequence(
    name="Jump Back Kick",
    steps=[
        InputStep(keys=["up", "right"], duration_frames=8),
        InputStep(keys="num_6", duration_frames=4)
    ]
)

# ---------------------------------------------------------
# NOTEPAD TEST SEQUENCES (Use these when testing on Notepad!)
# ---------------------------------------------------------
# Simple sequences that print recognizable text in Notepad
notepad_seq_1 = InputSequence(
    name="Type HELLO",
    steps=[
        InputStep(keys="h", duration_frames=5),
        InputStep(keys="e", duration_frames=5),
        InputStep(keys="l", duration_frames=5),
        InputStep(keys="l", duration_frames=5),
        InputStep(keys="o", duration_frames=5),
        InputStep(keys="space", duration_frames=5)
    ]
)

notepad_seq_2 = InputSequence(
    name="Type P2_BOT",
    steps=[
        InputStep(keys="shift", duration_frames=2), # Hold shift to uppercase P
        InputStep(keys=["shift", "p"], duration_frames=5),
        InputStep(keys="2", duration_frames=5),
        InputStep(keys="shift", duration_frames=2),
        InputStep(keys="b", duration_frames=5),
        InputStep(keys="o", duration_frames=5),
        InputStep(keys="t", duration_frames=5),
        InputStep(keys="enter", duration_frames=5)
    ]
)

# Define which list of sequences the controller will execute
# Switch between TEST_SEQUENCES (Notepad) and GAME_SEQUENCES (Fighting Game) here.
TEST_SEQUENCES = [notepad_seq_1, notepad_seq_2]
GAME_SEQUENCES = [hadouken_p2, shoryuken_p2, light_kick_p2, jump_back_kick_p2]

# Active sequence list to load
SEQUENCES = TEST_SEQUENCES  # Change to GAME_SEQUENCES for actual gameplay!
