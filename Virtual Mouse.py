"""
Virtual Mouse.py — Original script (updated to use pyautogui + more gestures).
For the full upgraded version with Kalman filter, dual-hand, voice & analytics,
run:  python main.py
"""

import cv2
import numpy as np
import time
import pyautogui          # replaces deprecated autopy
import HandTracking as ht

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ── Settings ────────────────────────────────────────────────────
WIDTH, HEIGHT = 640, 480
FRAME_R = 100          # Active-zone border in pixels
SMOOTHING = 7          # Lower = faster / jittery, higher = slower / smooth
CLICK_DIST = 40        # Pixel distance that triggers a left click
SCROLL_SPEED = 30      # pyautogui scroll units per tick
# ────────────────────────────────────────────────────────────────

prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0
p_time = 0
t_click = t_right = t_scroll = 0.0

cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

detector = ht.handDetector(maxHands=1)
screen_w, screen_h = pyautogui.size()

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)            # mirror so movement feels natural
    img = detector.findHands(img)
    lmlist, bbox = detector.findPosition(img)

    if lmlist:
        x1, y1 = lmlist[8][1], lmlist[8][2]   # index tip
        x2, y2 = lmlist[12][1], lmlist[12][2]  # middle tip
        fingers = detector.fingersUp()

        cv2.rectangle(img, (FRAME_R, FRAME_R), (WIDTH - FRAME_R, HEIGHT - FRAME_R),
                      (255, 0, 255), 2)

        now = time.time()

        # ── MOVE: index only ─────────────────────────────────
        if fingers[1] == 1 and fingers[2] == 0:
            tx = np.interp(x1, (FRAME_R, WIDTH - FRAME_R), (0, screen_w))
            ty = np.interp(y1, (FRAME_R, HEIGHT - FRAME_R), (0, screen_h))
            curr_x = prev_x + (tx - prev_x) / SMOOTHING
            curr_y = prev_y + (ty - prev_y) / SMOOTHING
            pyautogui.moveTo(curr_x, curr_y)
            cv2.circle(img, (x1, y1), 8, (0, 255, 100), cv2.FILLED)
            prev_x, prev_y = curr_x, curr_y

        # ── LEFT CLICK: index + middle close ─────────────────
        elif fingers[1] == 1 and fingers[2] == 1:
            length, img, li = detector.findDistance(8, 12, img)
            if length < CLICK_DIST and now - t_click > 0.4:
                cv2.circle(img, (li[4], li[5]), 13, (0, 255, 0), cv2.FILLED)
                pyautogui.click()
                t_click = now

        # ── RIGHT CLICK: index + pinky ────────────────────────
        elif fingers[1] == 1 and fingers[4] == 1 and fingers[2] == 0:
            if now - t_right > 0.6:
                pyautogui.rightClick()
                t_right = now
                cv2.putText(img, "Right Click", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

        # ── SCROLL: index + middle + ring ────────────────────
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            if now - t_scroll > 0.12:
                direction = 1 if y1 < HEIGHT // 2 else -1
                pyautogui.scroll(SCROLL_SPEED * direction)
                t_scroll = now
                label = "Scroll Up" if direction > 0 else "Scroll Down"
                cv2.putText(img, label, (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)

    c_time = time.time()
    fps = 1 / max(c_time - p_time, 1e-6)
    p_time = c_time
    cv2.putText(img, f"FPS: {int(fps)}", (20, 50),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.imshow("Virtual Mouse (legacy) — Q to quit", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
