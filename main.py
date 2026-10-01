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
import numpy as np
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


def draw_control_panel(canvas, start_x, fps, hand_detected, hand_label, cursor_ctrl, stable_gesture, camera_running, emergency_stop):
    """
    Draws a clean, professional sidebar UI on the right side of the canvas.
    """
    # Background color for panel (dark gray)
    canvas[:, start_x:] = (30, 30, 30)
    
    # Title
    cv2.putText(canvas, "AI VISION CONTROLLER", (start_x + 20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
    
    # Status Section
    y = 70
    if emergency_stop:
        cv2.putText(canvas, "EMERGENCY STOP: ON", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        y += 25
        cv2.putText(canvas, "Press 'R' to Resume", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        y += 25
    else:
        cv2.putText(canvas, "EMERGENCY STOP: OFF", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        y += 25

    cam_status = "ACTIVE" if camera_running else "STOPPED"
    cam_color = (0, 255, 0) if camera_running else (0, 0, 255)
    cv2.putText(canvas, f"Camera: {cam_status}", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cam_color, 1)
    
    y += 25
    cv2.putText(canvas, f"FPS: {fps:.1f}", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    y += 25
    if hand_detected:
        hand_text = f"Hand: DETECTED ({hand_label})"
        hand_color = (0, 255, 0)
    else:
        hand_text = "Hand: NOT DETECTED"
        hand_color = (0, 0, 255)
    cv2.putText(canvas, hand_text, (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hand_color, 1)
    
    y += 25
    cv2.putText(canvas, f"Gesture: {stable_gesture}", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    y += 25
    if cursor_ctrl.is_paused:
        pause_text = "Control: PAUSED"
        pause_color = (0, 0, 255)
    else:
        pause_text = "Control: ACTIVE"
        pause_color = (0, 255, 0)
    cv2.putText(canvas, pause_text, (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, pause_color, 1)
    
    y += 40
    # Action Status Section
    cv2.putText(canvas, "ACTION STATUS", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)
    y += 25
    
    def draw_status(label, is_active, y_pos):
        color = (0, 255, 0) if is_active else (100, 100, 100)
        state = "ON" if is_active else "OFF"
        cv2.putText(canvas, f"{label}: {state}", (start_x + 20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return y_pos + 25

    y = draw_status("Left Click", cursor_ctrl.is_pinching, y)
    y = draw_status("Right Click", cursor_ctrl.is_right_pinching, y)
    y = draw_status("Scroll", stable_gesture == "SCROLL", y)
    y = draw_status("Enter", cursor_ctrl.is_thumbs_up_active, y)
    y = draw_status("Escape", cursor_ctrl.is_fist_active, y)
    
    y += 15
    # Help Section
    cv2.putText(canvas, "GESTURE GUIDE", (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)
    y += 25
    
    guide = [
        "[1 Finger] Cursor",
        "[Pinch] Left Click",
        "[2 Fingers] Scroll",
        "[Mid Pinch] Right Click",
        "[Thumbs Up] Enter",
        "[Open Palm] Pause",
        "[Fist] Escape",
        "",
        "Press 'ESC' for Emergency Stop",
        "Press 'R' to Resume Control",
        "Press 'S' to Stop/Start Cam",
        "Press 'Q' to Quit"
    ]
    for text in guide:
        cv2.putText(canvas, text, (start_x + 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        y += 20

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

    # --- State ---
    prev_time = time.time()
    fps = 0.0
    camera_running = True
    emergency_stop = False

    try:
        while True:
            # --- Handle key presses ---
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("[INFO] Quit requested by user.")
                break
            elif key == 27:  # 27 = ESC
                emergency_stop = True
                print("[INFO] EMERGENCY STOP ACTIVATED.")
            elif key == ord('r') or key == ord('R'):
                emergency_stop = False
                print("[INFO] Control resumed.")
            elif key == ord('s') or key == ord('S'):
                camera_running = not camera_running
                print(f"[INFO] Camera running: {camera_running}")

            ret, frame = cap.read()

            if not ret:
                print("[ERROR] Failed to read frame from webcam.")
                print("        Camera may have been disconnected.")
                break

            # Flip horizontally so movements feel natural (mirror view)
            frame = cv2.flip(frame, 1)
            frame_h, frame_w = frame.shape[:2]
            
            # --- Create UI Canvas ---
            panel_w = 320
            canvas = np.zeros((frame_h, frame_w + panel_w, 3), dtype=np.uint8)
            
            # Default state when camera is stopped
            hand_detected = False
            stable_gesture = "NONE"
            
            if camera_running:
                # Put the camera frame on the left
                canvas[:, :frame_w] = frame
                
                # --- Hand tracking ---
                hand_detected = tracker.process(frame)
                fingers = tracker.get_raised_fingers()
    
                # --- Draw active region rectangle ---
                draw_active_region(canvas[:, :frame_w], cursor_ctrl)
    
                # --- Cursor movement, Clicking, Scrolling, & Thumbs Up (Phase 2-9) ---
            finger_pos = None
            thumb_pos = None
            middle_pos = None
            raw_gesture = "NONE"
            
            if hand_detected:
                # Get index finger tip (landmark 8), thumb tip (landmark 4), and middle tip (landmark 12)
                finger_pos = tracker.get_landmark_coords(8, frame_w, frame_h)
                thumb_pos = tracker.get_landmark_coords(4, frame_w, frame_h)
                middle_pos = tracker.get_landmark_coords(12, frame_w, frame_h)
                
                if tracker.is_open_palm():
                    raw_gesture = "PAUSE"
                elif tracker.is_fist():
                    raw_gesture = "FIST"
                elif fingers == [1, 1, 0, 0]:
                    raw_gesture = "SCROLL"
                elif tracker.is_thumbs_up():
                    raw_gesture = "THUMBS_UP"
                elif finger_pos is not None and thumb_pos is not None:
                    # Check pinch distances for left/right click
                    dist_left = math.hypot(finger_pos[0] - thumb_pos[0], finger_pos[1] - thumb_pos[1])
                    if middle_pos is not None:
                        dist_right = math.hypot(middle_pos[0] - thumb_pos[0], middle_pos[1] - thumb_pos[1])
                    else:
                        dist_right = float('inf')
                        
                    if dist_left < config.PINCH_THRESHOLD:
                        raw_gesture = "LEFT_CLICK"
                    elif dist_right < config.RIGHT_CLICK_THRESHOLD:
                        raw_gesture = "RIGHT_CLICK"
                    else:
                        raw_gesture = "CURSOR"
                else:
                    raw_gesture = "CURSOR"
            
            # --- Phase 9 Stability ---
            if hand_detected:
                stable_gesture = cursor_ctrl.update_gesture_history(raw_gesture)
            else:
                stable_gesture = "NONE"
                cursor_ctrl.reset()
                
            # --- Phase 11 Emergency Stop Override ---
            if emergency_stop:
                stable_gesture = "NONE"
                cursor_ctrl.reset()
                cursor_ctrl.is_paused = True
                
            # Execute actions based on stable gesture
            if stable_gesture == "PAUSE":
                cursor_ctrl.is_paused = True
            else:
                cursor_ctrl.is_paused = False
                
                if stable_gesture in ["CURSOR", "LEFT_CLICK", "RIGHT_CLICK"] and finger_pos is not None:
                    cursor_ctrl.end_scroll()
                    cursor_ctrl.handle_thumbs_up(False)
                    cursor_ctrl.handle_fist(False)
                    cursor_ctrl.move(finger_pos[0], finger_pos[1], frame_w, frame_h)
                    
                    if stable_gesture == "LEFT_CLICK":
                        cursor_ctrl.trigger_left_click()
                    else:
                        cursor_ctrl.is_pinching = False
                        
                    if stable_gesture == "RIGHT_CLICK":
                        cursor_ctrl.trigger_right_click()
                    else:
                        cursor_ctrl.is_right_pinching = False
                        
                elif stable_gesture == "SCROLL" and finger_pos is not None and middle_pos is not None:
                    cursor_ctrl.handle_thumbs_up(False)
                    cursor_ctrl.handle_fist(False)
                    cursor_ctrl.is_pinching = False
                    cursor_ctrl.is_right_pinching = False
                    avg_y = (finger_pos[1] + middle_pos[1]) / 2.0
                    cursor_ctrl.handle_scroll(avg_y)
                    
                elif stable_gesture == "THUMBS_UP":
                    cursor_ctrl.end_scroll()
                    cursor_ctrl.handle_fist(False)
                    cursor_ctrl.is_pinching = False
                    cursor_ctrl.is_right_pinching = False
                    cursor_ctrl.handle_thumbs_up(True)
                    
                elif stable_gesture == "FIST":
                    cursor_ctrl.end_scroll()
                    cursor_ctrl.handle_thumbs_up(False)
                    cursor_ctrl.is_pinching = False
                    cursor_ctrl.is_right_pinching = False
                    cursor_ctrl.handle_fist(True)


            if camera_running:
                # --- Draw landmarks on frame ---
                tracker.draw_landmarks(canvas[:, :frame_w])
    
                # --- Draw highlighted index finger dot ---
                draw_index_finger_dot(canvas[:, :frame_w], finger_pos)
            else:
                # If camera is stopped, just put a message on the blank left side
                cv2.putText(canvas, "CAMERA STOPPED", (frame_w // 2 - 120, frame_h // 2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cursor_ctrl.reset()

            # --- Calculate FPS ---
            current_time = time.time()
            elapsed = current_time - prev_time
            if elapsed > 0:
                fps = 1.0 / elapsed
            prev_time = current_time

            # --- Draw Control Panel ---
            draw_control_panel(canvas, frame_w, fps, hand_detected, tracker.hand_label, cursor_ctrl, stable_gesture, camera_running, emergency_stop)

            # --- Show frame ---
            cv2.imshow(config.WINDOW_NAME, canvas)

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
