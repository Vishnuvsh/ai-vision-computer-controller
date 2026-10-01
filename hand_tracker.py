# ============================================================
# hand_tracker.py — MediaPipe hand tracking module
# ============================================================
# Encapsulates all MediaPipe hand detection logic.
# Returns landmark data for the main loop to use.
# ============================================================

import mediapipe as mp
import cv2
import config


class HandTracker:
    """Wraps MediaPipe Hands for single-hand detection and drawing."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MAX_NUM_HANDS,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )

        # Custom drawing specs
        self.landmark_style = self.mp_drawing.DrawingSpec(
            color=config.LANDMARK_COLOR,
            thickness=-1,  # filled circle
            circle_radius=config.LANDMARK_RADIUS,
        )
        self.connection_style = self.mp_drawing.DrawingSpec(
            color=config.CONNECTION_COLOR,
            thickness=config.CONNECTION_THICKNESS,
        )

        # State
        self.hand_detected = False
        self.landmarks = None       # NormalizedLandmarkList for the first hand
        self.hand_label = None       # "Left" or "Right"

    def process(self, frame):
        """
        Process a BGR frame, detect hands, and update internal state.

        Args:
            frame: BGR image (numpy array) from OpenCV.

        Returns:
            True if a hand was detected, False otherwise.
        """
        # MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Improve performance by marking the image as not writeable
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
            self.hand_detected = True
            self.landmarks = results.multi_hand_landmarks[0]

            # Get handedness label (Left/Right)
            if results.multi_handedness and len(results.multi_handedness) > 0:
                self.hand_label = results.multi_handedness[0].classification[0].label
            else:
                self.hand_label = "Unknown"
        else:
            self.hand_detected = False
            self.landmarks = None
            self.hand_label = None

        return self.hand_detected

    def draw_landmarks(self, frame):
        """
        Draw the 21 hand landmarks and connections onto the frame.

        Args:
            frame: BGR image to draw on (modified in-place).
        """
        if self.landmarks is not None:
            self.mp_drawing.draw_landmarks(
                frame,
                self.landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.landmark_style,
                self.connection_style,
            )

    def get_landmark_coords(self, landmark_id, frame_width, frame_height):
        """
        Get pixel coordinates of a specific landmark.

        Args:
            landmark_id: MediaPipe landmark index (0-20).
            frame_width: Width of the camera frame.
            frame_height: Height of the camera frame.

        Returns:
            (x, y) in pixel coordinates, or None if no hand detected.
        """
        if self.landmarks is None:
            return None

        lm = self.landmarks.landmark[landmark_id]
        x = int(lm.x * frame_width)
        y = int(lm.y * frame_height)
        return (x, y)

    def get_raised_fingers(self):
        """
        Returns a list of 1s (raised) and 0s (folded) for the 4 fingers 
        (Index, Middle, Ring, Pinky). Thumb is ignored for simplicity.
        """
        if self.landmarks is None:
            return [0, 0, 0, 0]

        fingers = []
        # Tip and PIP (Proximal Interphalangeal) joint IDs for the 4 fingers
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]

        for tip, pip in zip(tip_ids, pip_ids):
            # In image coordinates, smaller Y is higher (closer to top of screen)
            if self.landmarks.landmark[tip].y < self.landmarks.landmark[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def is_thumbs_up(self):
        """
        Detects if the hand is making a thumbs-up gesture.
        Heuristic: 
        1. All 4 fingers are folded.
        2. Thumb tip (4) is higher (smaller Y) than the thumb MCP (2) and index MCP (5).
        """
        if self.landmarks is None:
            return False

        fingers = self.get_raised_fingers()
        # Ensure Index, Middle, Ring, Pinky are all folded
        if fingers == [0, 0, 0, 0]:
            thumb_tip = self.landmarks.landmark[4]
            thumb_mcp = self.landmarks.landmark[2]
            index_mcp = self.landmarks.landmark[5]
            
            # Check if thumb tip is clearly pointing up relative to the knuckles
            if thumb_tip.y < thumb_mcp.y and thumb_tip.y < index_mcp.y:
                return True
                
        return False

    def is_open_palm(self):
        """
        Detects if the hand is making an open palm gesture.
        Heuristic: 
        1. All 4 fingers (Index, Middle, Ring, Pinky) are raised.
        """
        if self.landmarks is None:
            return False

        fingers = self.get_raised_fingers()
        # Check if Index, Middle, Ring, Pinky are all raised
        if fingers == [1, 1, 1, 1]:
            return True
            
        return False

    def is_fist(self):
        """
        Detects if the hand is making a closed fist.
        Heuristic:
        1. All 4 fingers are folded.
        2. The thumb is NOT in a thumbs-up position.
        """
        if self.landmarks is None:
            return False
            
        fingers = self.get_raised_fingers()
        if fingers == [0, 0, 0, 0] and not self.is_thumbs_up():
            return True
            
        return False

    def release(self):
        """Release MediaPipe resources."""
        self.hands.close()
