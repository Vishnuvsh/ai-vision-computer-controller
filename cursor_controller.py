# ============================================================
# cursor_controller.py — Phase 2: Cursor Movement
# ============================================================
# Maps index finger tip position to screen coordinates with
# smoothing. Handles active region and coordinate mapping.
# ============================================================

import pyautogui
import config


class CursorController:
    """Controls the mouse cursor based on hand landmark positions."""

    def __init__(self):
        # --- Detect screen resolution ---
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"[INFO] Screen resolution: {self.screen_width}x{self.screen_height}")

        # Disable pyautogui's failsafe and built-in pause for real-time use.
        # We'll implement our own safety mechanisms in later phases.
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

        # --- Smoothing state ---
        self.prev_x = self.screen_width / 2.0
        self.prev_y = self.screen_height / 2.0
        self.is_initialized = False

        # --- Control state ---
        self.cursor_active = False  # True when hand is detected and finger is in region

    def get_active_region(self, frame_width, frame_height):
        """
        Calculate the active control region boundaries in pixel coordinates.
        The active region is the inner portion of the camera frame,
        excluding margins on all sides.

        Returns:
            (x1, y1, x2, y2) — top-left and bottom-right of active region.
        """
        margin_x = int(frame_width * config.ACTIVE_REGION_MARGIN_X)
        margin_y = int(frame_height * config.ACTIVE_REGION_MARGIN_Y)

        x1 = margin_x
        y1 = margin_y
        x2 = frame_width - margin_x
        y2 = frame_height - margin_y

        return x1, y1, x2, y2

    def is_in_active_region(self, finger_x, finger_y, frame_width, frame_height):
        """Check if the finger position is within the active control region."""
        x1, y1, x2, y2 = self.get_active_region(frame_width, frame_height)
        return x1 <= finger_x <= x2 and y1 <= finger_y <= y2

    def map_to_screen(self, finger_x, finger_y, frame_width, frame_height):
        """
        Map finger pixel coordinates (within the active region)
        to screen coordinates.

        Finger positions are clamped to the active region boundaries
        so the cursor can always reach screen edges.
        """
        x1, y1, x2, y2 = self.get_active_region(frame_width, frame_height)

        # Clamp finger position to active region
        clamped_x = max(x1, min(x2, finger_x))
        clamped_y = max(y1, min(y2, finger_y))

        # Normalize to 0.0 — 1.0 within active region
        region_width = x2 - x1
        region_height = y2 - y1

        if region_width == 0 or region_height == 0:
            return self.screen_width // 2, self.screen_height // 2

        norm_x = (clamped_x - x1) / region_width
        norm_y = (clamped_y - y1) / region_height

        # Map to screen coordinates
        screen_x = norm_x * self.screen_width
        screen_y = norm_y * self.screen_height

        return screen_x, screen_y

    def move(self, finger_x, finger_y, frame_width, frame_height):
        """
        Move the mouse cursor to the mapped position with smoothing.

        Args:
            finger_x, finger_y: Index finger tip position in camera pixels.
            frame_width, frame_height: Camera frame dimensions.

        Returns:
            (smooth_x, smooth_y) — the final cursor position on screen,
            or None if the finger is outside the active region.
        """
        # Check if finger is in the active region
        if not self.is_in_active_region(finger_x, finger_y, frame_width, frame_height):
            self.cursor_active = False
            return None

        self.cursor_active = True

        # Map to screen coordinates
        target_x, target_y = self.map_to_screen(
            finger_x, finger_y, frame_width, frame_height
        )

        # On first detection, jump directly to position (no smoothing)
        if not self.is_initialized:
            self.prev_x = target_x
            self.prev_y = target_y
            self.is_initialized = True

        # Apply exponential smoothing
        # Higher CURSOR_SMOOTHING = more smoothing = slower but stabler
        # Lower CURSOR_SMOOTHING = less smoothing = faster but shakier
        smoothing = config.CURSOR_SMOOTHING
        smooth_x = self.prev_x * smoothing + target_x * (1 - smoothing)
        smooth_y = self.prev_y * smoothing + target_y * (1 - smoothing)

        # Clamp to screen bounds
        smooth_x = max(0, min(self.screen_width - 1, smooth_x))
        smooth_y = max(0, min(self.screen_height - 1, smooth_y))

        # Move the OS cursor
        pyautogui.moveTo(int(smooth_x), int(smooth_y))

        # Save for next frame
        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return int(smooth_x), int(smooth_y)

    def reset(self):
        """Reset cursor tracking state (e.g., when hand disappears)."""
        self.is_initialized = False
        self.cursor_active = False
