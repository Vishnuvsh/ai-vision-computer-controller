# ============================================================
# config.py — Centralized configuration for gesture control
# ============================================================
# All tunable parameters live here so they can be adjusted
# without modifying core logic.
# New parameters will be added as phases progress.
# ============================================================

# --- Camera Settings ---
CAMERA_INDEX = 0              # Default webcam
CAMERA_BACKEND = "DSHOW"      # Use DirectShow on Windows (MSMF fails on many systems)
CAMERA_WIDTH = 640            # Capture width
CAMERA_HEIGHT = 480           # Capture height
CAMERA_FPS = 30               # Target FPS

# --- MediaPipe Hand Tracking Settings ---
MAX_NUM_HANDS = 1             # Detect one hand only
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6

# --- Display Settings ---
WINDOW_NAME = "Gesture Control — Phase 2"
SHOW_FPS = True
SHOW_HAND_STATUS = True

# --- Landmark Drawing Styles ---
LANDMARK_COLOR = (0, 255, 0)       # Green dots for landmarks
LANDMARK_RADIUS = 5
CONNECTION_COLOR = (255, 255, 255)  # White lines for connections
CONNECTION_THICKNESS = 2

# --- UI Text Settings ---
FONT_SCALE = 0.8
FONT_THICKNESS = 2
TEXT_COLOR_GREEN = (0, 255, 0)
TEXT_COLOR_RED = (0, 0, 255)
TEXT_COLOR_WHITE = (255, 255, 255)
FPS_POSITION = (10, 30)
STATUS_POSITION = (10, 65)
CURSOR_INFO_POSITION = (10, 100)

# --- Cursor Control Settings (Phase 2) ---
CURSOR_SMOOTHING = 0.7          # 0.0 = no smoothing (raw), 1.0 = max smoothing (frozen)
                                # Recommended range: 0.5 — 0.8
ACTIVE_REGION_MARGIN_X = 0.12   # 12% margin on left and right edges
ACTIVE_REGION_MARGIN_Y = 0.15   # 15% margin on top and bottom edges
ACTIVE_REGION_COLOR = (255, 255, 0)  # Cyan rectangle for active region
ACTIVE_REGION_THICKNESS = 2
INDEX_FINGER_DOT_COLOR = (0, 0, 255)  # Red dot on index finger tip
INDEX_FINGER_DOT_RADIUS = 10
