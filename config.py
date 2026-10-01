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
WINDOW_NAME = "Gesture Control — Final Phase"
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

# --- Cursor Control Settings (Phase 2, 3, 4, 5, & 6) ---
CURSOR_SMOOTHING = 0.7          # 0.0 = no smoothing (raw), 1.0 = max smoothing (frozen)
                                # Recommended range: 0.5 — 0.8
ACTIVE_REGION_MARGIN_X = 0.12   # 12% margin on left and right edges
ACTIVE_REGION_MARGIN_Y = 0.15   # 15% margin on top and bottom edges
ACTIVE_REGION_COLOR = (255, 255, 0)  # Cyan rectangle for active region
ACTIVE_REGION_THICKNESS = 2
INDEX_FINGER_DOT_COLOR = (0, 0, 255)  # Red dot on index finger tip
INDEX_FINGER_DOT_RADIUS = 10

# --- Pinch / Click Settings (Phase 3) ---
PINCH_THRESHOLD = 30            # Pixel distance between thumb and index finger to trigger pinch
CLICK_COOLDOWN = 0.5            # Minimum seconds between clicks to prevent double-clicking

# --- Scroll Settings (Phase 4) ---
SCROLL_SENSITIVITY = 15         # Multiplier for scroll distance (Windows typically uses increments of 120)
SCROLL_DEAD_ZONE = 10           # Pixel movement required before scrolling starts

# --- Right Click Settings (Phase 5) ---
RIGHT_CLICK_THRESHOLD = 30
RIGHT_CLICK_COOLDOWN = 0.5

# --- Thumbs Up Settings (Phase 6) ---
THUMBS_UP_COOLDOWN = 1.0

# --- Open Palm Pause Settings (Phase 7) ---
# Pause stability is now handled by the global Phase 9 Gesture Stability

# --- Fist Settings (Phase 8) ---
FIST_COOLDOWN = 1.0

# --- Gesture Stability Settings (Phase 9) ---
STABILITY_FRAMES = 5             # Number of consistent frames to confirm a gesture
