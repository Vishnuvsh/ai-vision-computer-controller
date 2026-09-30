# ============================================================
# main.py — Phase 2: Webcam + Hand Tracking + Cursor Movement
# ============================================================
# Opens the webcam, runs MediaPipe hand detection,
# draws landmarks & connections, shows FPS and hand status,
# and moves the mouse cursor using index finger tip.
#
# Press 'Q' or ESC to quit.
# ============================================================

import sys
import time
import cv2
import config
from hand_tracker import HandTracker
from cursor_controller import CursorController


def initialize_camera():
    """
    Open the webcam and configure resolution.
    Uses DirectShow backend on Windows for reliability.

    Returns:
        cv2.VideoCapture object, or None on failure.
    """
    # Map backend string to OpenCV constant
    backend_map = {
        "DSHOW": cv2.CAP_DSHOW,
        "MSMF": cv2.CAP_MSMF,
        "ANY": cv2.CAP_ANY,
    }
    backend = backend_map.get(config.CAMERA_BACKEND, cv2.CAP_ANY)
    backend_name = config.CAMERA_BACKEND

    print(f"[INFO] Opening camera index {config.CAMERA_INDEX} with {backend_name} backend...")
    cap = cv2.VideoCapture(config.CAMERA_INDEX, backend)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        print("        Possible causes:")
        print("        - No webcam connected")
        print("        - Camera in use by another application")
        print("        - Incorrect CAMERA_INDEX in config.py")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

    # Read actual values (camera may not support requested settings)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[INFO] Camera opened: {actual_w}x{actual_h} @ {actual_fps:.0f} FPS")

    return cap


def draw_active_region(frame, cursor_ctrl):
    """Draw the active control region rectangle on the frame."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = cursor_ctrl.get_active_region(w, h)

    cv2.rectangle(
        frame,
        (x1, y1), (x2, y2),
        config.ACTIVE_REGION_COLOR,
        config.ACTIVE_REGION_THICKNESS,
    )


def draw_index_finger_dot(frame, finger_pos):
    """Draw a highlighted dot on the index finger tip."""
    if finger_pos is not None:
        cv2.circle(
            frame,
            finger_pos,
            config.INDEX_FINGER_DOT_RADIUS,
            config.INDEX_FINGER_DOT_COLOR,
            -1,  # filled
        )


def draw_overlay(frame, fps, hand_detected, hand_label, cursor_ctrl):
    """
    Draw FPS counter, hand-detection status, and cursor info onto the frame.
    """
    h, w = frame.shape[:2]

    # --- Semi-transparent background bar for readability ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 260), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # --- FPS ---
    if config.SHOW_FPS:
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(
            frame, fps_text,
            config.FPS_POSITION,
            cv2.FONT_HERSHEY_SIMPLEX,
            config.FONT_SCALE,
            config.TEXT_COLOR_WHITE,
            config.FONT_THICKNESS,
            cv2.LINE_AA,
        )

    # --- Hand Status ---
    if config.SHOW_HAND_STATUS:
        if hand_detected:
            status_text = f"Hand Detected ({hand_label})"
            color = config.TEXT_COLOR_GREEN
        else:
            status_text = "No Hand"
            color = config.TEXT_COLOR_RED

        cv2.putText(
            frame, status_text,
            config.STATUS_POSITION,
            cv2.FONT_HERSHEY_SIMPLEX,
            config.FONT_SCALE,
            color,
            config.FONT_THICKNESS,
            cv2.LINE_AA,
        )

    # --- Cursor Control Status (Phase 2) ---
    if cursor_ctrl.cursor_active:
        cursor_text = f"Cursor: ACTIVE  |  Screen: {cursor_ctrl.screen_width}x{cursor_ctrl.screen_height}"
        cursor_color = config.TEXT_COLOR_GREEN
    else:
        if hand_detected:
            cursor_text = "Cursor: OUT OF REGION"
            cursor_color = (0, 165, 255)  # Orange
        else:
            cursor_text = f"Cursor: INACTIVE  |  Screen: {cursor_ctrl.screen_width}x{cursor_ctrl.screen_height}"
            cursor_color = config.TEXT_COLOR_RED

    cv2.putText(
        frame, cursor_text,
        config.CURSOR_INFO_POSITION,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        cursor_color,
        config.FONT_THICKNESS,
        cv2.LINE_AA,
    )

    # --- Pinch Status (Phase 3) ---
    if cursor_ctrl.is_pinching:
        pinch_text = "Pinch: ON (Click!)"
        pinch_color = config.TEXT_COLOR_GREEN
    else:
        pinch_text = "Pinch: OFF"
        pinch_color = config.TEXT_COLOR_RED

    cv2.putText(
        frame, pinch_text,
        config.PINCH_INFO_POSITION,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        pinch_color,
        config.FONT_THICKNESS,
        cv2.LINE_AA,
    )

    # --- Scroll Status (Phase 4) ---
    if cursor_ctrl.is_scrolling:
        scroll_text = "Scroll: ON"
        scroll_color = config.TEXT_COLOR_GREEN
    else:
        scroll_text = "Scroll: OFF"
        scroll_color = config.TEXT_COLOR_RED

    cv2.putText(
        frame, scroll_text,
        config.SCROLL_INFO_POSITION,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        scroll_color,
        config.FONT_THICKNESS,
        cv2.LINE_AA,
    )

    # --- Right Click Status (Phase 5) ---
    if cursor_ctrl.is_right_pinching:
        rc_text = "Right Click: ON (Click!)"
        rc_color = config.TEXT_COLOR_GREEN
    else:
        rc_text = "Right Click: OFF"
        rc_color = config.TEXT_COLOR_RED

    cv2.putText(
        frame, rc_text,
        config.RIGHT_CLICK_INFO_POSITION,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        rc_color,
        config.FONT_THICKNESS,
        cv2.LINE_AA,
    )

    # --- Thumbs Up Status (Phase 6) ---
    if cursor_ctrl.is_thumbs_up_active:
        tu_text = "Thumbs Up: ON (Enter!)"
        tu_color = config.TEXT_COLOR_GREEN
    else:
        tu_text = "Thumbs Up: OFF"
        tu_color = config.TEXT_COLOR_RED

    cv2.putText(
        frame, tu_text,
        config.THUMBS_UP_INFO_POSITION,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        tu_color,
        config.FONT_THICKNESS,
        cv2.LINE_AA,
    )



def main():
    # --- Initialize camera ---
    cap = initialize_camera()
    if cap is None:
        sys.exit(1)

    # --- Initialize hand tracker ---
    tracker = HandTracker()
    print("[INFO] Hand tracker initialized.")

    # --- Initialize cursor controller (Phase 2) ---
    cursor_ctrl = CursorController()
    print("[INFO] Cursor controller initialized.")
    print("[INFO] Press 'Q' or ESC to quit.\n")

    # --- FPS calculation ---
    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("[ERROR] Failed to read frame from webcam.")
                print("        Camera may have been disconnected.")
                break

            # Flip horizontally so movements feel natural (mirror view)
            frame = cv2.flip(frame, 1)
            frame_h, frame_w = frame.shape[:2]

            # --- Hand tracking ---
            hand_detected = tracker.process(frame)
            fingers = tracker.get_raised_fingers()

            # --- Draw active region rectangle ---
            draw_active_region(frame, cursor_ctrl)

            # --- Cursor movement, Clicking, Scrolling, & Thumbs Up (Phase 2-6) ---
            finger_pos = None
            thumb_pos = None
            middle_pos = None
            if hand_detected:
                # Get index finger tip (landmark 8), thumb tip (landmark 4), and middle tip (landmark 12)
                finger_pos = tracker.get_landmark_coords(8, frame_w, frame_h)
                thumb_pos = tracker.get_landmark_coords(4, frame_w, frame_h)
                middle_pos = tracker.get_landmark_coords(12, frame_w, frame_h)
                is_thumbs_up_gesture = tracker.is_thumbs_up()

                if finger_pos is not None:
                    # Check if Index and Middle fingers are raised, and Ring/Pinky are folded
                    # [Index, Middle, Ring, Pinky]
                    if fingers == [1, 1, 0, 0]:
                        # Scroll Mode
                        cursor_ctrl.handle_thumbs_up(False)
                        if middle_pos is not None:
                            # Use average Y coordinate of index and middle fingers for smoother scrolling
                            avg_y = (finger_pos[1] + middle_pos[1]) / 2.0
                            cursor_ctrl.handle_scroll(avg_y)
                    elif is_thumbs_up_gesture:
                        # Thumbs Up Mode
                        cursor_ctrl.end_scroll()
                        cursor_ctrl.handle_thumbs_up(True)
                    else:
                        # Cursor Mode (Movement and Pinch)
                        cursor_ctrl.end_scroll()
                        cursor_ctrl.handle_thumbs_up(False)
                        
                        # Move cursor based on finger position
                        cursor_ctrl.move(finger_pos[0], finger_pos[1], frame_w, frame_h)
                
                        if thumb_pos is not None:
                            # Handle left click (thumb + index)
                            cursor_ctrl.handle_click(thumb_pos[0], thumb_pos[1], finger_pos[0], finger_pos[1])
                            
                            if middle_pos is not None:
                                # Handle right click (thumb + middle)
                                cursor_ctrl.handle_right_click(thumb_pos[0], thumb_pos[1], middle_pos[0], middle_pos[1])
            else:
                # No hand → reset state
                cursor_ctrl.reset()


            # --- Draw landmarks on frame ---
            tracker.draw_landmarks(frame)

            # --- Draw highlighted index finger dot ---
            draw_index_finger_dot(frame, finger_pos)

            # --- Calculate FPS ---
            current_time = time.time()
            elapsed = current_time - prev_time
            if elapsed > 0:
                fps = 1.0 / elapsed
            prev_time = current_time

            # --- Draw overlay (FPS + status + cursor info) ---
            draw_overlay(frame, fps, hand_detected, tracker.hand_label, cursor_ctrl)

            # --- Show frame ---
            cv2.imshow(config.WINDOW_NAME, frame)

            # --- Handle key presses ---
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:  # 27 = ESC
                print("[INFO] Quit requested by user.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user (Ctrl+C).")

    finally:
        # --- Cleanup ---
        print("[INFO] Releasing resources...")
        tracker.release()
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Done.")


if __name__ == "__main__":
    main()
