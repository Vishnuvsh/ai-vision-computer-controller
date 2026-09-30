# ============================================================
# cursor_controller.py — Phase 2: Cursor Movement
# ============================================================
# Maps index finger tip position to screen coordinates with
# smoothing. Handles active region and coordinate mapping.
# ============================================================

import pyautogui
import math
import time
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
        self.is_pinching = False    # True when fingers are together
        self.last_click_time = 0.0  # Used for click debounce/cooldown
        
        # --- Scroll state ---
        self.is_scrolling = False
        self.prev_scroll_y = None
        
        # --- Right click state ---
        self.is_right_pinching = False
        self.last_right_click_time = 0.0
        
        # --- Thumbs up state ---
        self.is_thumbs_up_active = False
        self.last_enter_time = 0.0

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

    def handle_click(self, thumb_x, thumb_y, index_x, index_y):
        """
        Check distance between thumb and index finger.
        Perform a left click if pinched and cooldown has passed.
        
        Args:
            thumb_x, thumb_y: Pixel coordinates of the thumb tip.
            index_x, index_y: Pixel coordinates of the index finger tip.
            
        Returns:
            Boolean indicating if currently pinching.
        """
        # Calculate Euclidean distance between thumb and index
        distance = math.hypot(index_x - thumb_x, index_y - thumb_y)
        
        current_time = time.time()
        
        if distance < config.PINCH_THRESHOLD:
            if not self.is_pinching:
                # Pinch just started, check cooldown and prevent conflict with right click
                if not self.is_right_pinching and (current_time - self.last_click_time) > config.CLICK_COOLDOWN:
                    pyautogui.click()
                    self.last_click_time = current_time
                # Set state to pinching so we don't click again until release
                self.is_pinching = True
        else:
            # Fingers separated, reset pinch state
            self.is_pinching = False
            
        return self.is_pinching

    def handle_right_click(self, thumb_x, thumb_y, middle_x, middle_y):
        """
        Check distance between thumb and middle finger.
        Perform a right click if pinched and cooldown has passed.
        """
        distance = math.hypot(middle_x - thumb_x, middle_y - thumb_y)
        current_time = time.time()
        
        if distance < config.RIGHT_CLICK_THRESHOLD:
            if not self.is_right_pinching:
                # Pinch just started, check cooldown and prevent conflict with left click
                if not self.is_pinching and (current_time - self.last_right_click_time) > config.RIGHT_CLICK_COOLDOWN:
                    pyautogui.rightClick()
                    self.last_right_click_time = current_time
                self.is_right_pinching = True
        else:
            self.is_right_pinching = False
            
        return self.is_right_pinching

    def handle_scroll(self, y_pos):
        """
        Determine scroll amount based on vertical movement of fingers.
        Args:
            y_pos: Current Y position of the fingers in pixel coordinates.
        """
        self.is_scrolling = True
        
        if self.prev_scroll_y is None:
            self.prev_scroll_y = y_pos
            return
            
        delta_y = y_pos - self.prev_scroll_y
        
        # Only scroll if movement exceeds dead zone (prevents jitter)
        if abs(delta_y) > config.SCROLL_DEAD_ZONE:
            # PyAutoGUI scroll on Windows: Positive = Up, Negative = Down
            # If fingers move down (delta_y > 0), we want to scroll down (negative)
            scroll_amount = -int(delta_y * config.SCROLL_SENSITIVITY)
            pyautogui.scroll(scroll_amount)
            # Update previous Y to current Y
            self.prev_scroll_y = y_pos

    def end_scroll(self):
        """Reset scroll tracking when scroll gesture ends."""
        self.is_scrolling = False
        self.prev_scroll_y = None

    def handle_thumbs_up(self, is_detected):
        """
        Triggers Enter key if thumbs up is detected, with debounce.
        """
        current_time = time.time()
        
        if is_detected:
            if not self.is_thumbs_up_active:
                if (current_time - self.last_enter_time) > config.THUMBS_UP_COOLDOWN:
                    pyautogui.press('enter')
                    self.last_enter_time = current_time
                self.is_thumbs_up_active = True
        else:
            self.is_thumbs_up_active = False

    def reset(self):
        """Reset cursor tracking state (e.g., when hand disappears)."""
        self.is_initialized = False
        self.cursor_active = False
        self.is_pinching = False
        self.is_right_pinching = False
        self.is_thumbs_up_active = False
        self.end_scroll()

