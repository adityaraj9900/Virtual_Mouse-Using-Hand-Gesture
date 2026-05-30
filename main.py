"""
Virtual Mouse — Upgraded Main Entry Point
==========================================
Keyboard shortcuts while running:
  S  — open Settings GUI
  A  — open Analytics dashboard
  R  — reset per-user calibration
  Q  — quit
"""

import cv2
import numpy as np
import time
import queue
import sys
import os


def _setup_frozen_env():
    """When running as a PyInstaller .exe/.app, redirect writable data to the
    user's app-data folder and copy bundled defaults there on first launch."""
    if not getattr(sys, "frozen", False):
        return

    if sys.platform == "darwin":
        app_dir = os.path.expanduser("~/Library/Application Support/VirtualMouse")
    elif sys.platform == "win32":
        app_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "VirtualMouse")
    else:
        app_dir = os.path.expanduser("~/.local/share/VirtualMouse")

    os.makedirs(app_dir, exist_ok=True)
    os.chdir(app_dir)

    import shutil
    bundle = sys._MEIPASS  # type: ignore[attr-defined]
    for folder in ("profiles", "macros"):
        src = os.path.join(bundle, folder)
        dst = os.path.join(app_dir, folder)
        if os.path.isdir(src) and not os.path.isdir(dst):
            shutil.copytree(src, dst)

    # Ensure src/ and gui/ are importable from the bundle
    sys.path.insert(0, bundle)


_setup_frozen_env()

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.hand_tracking import HandDetector
from src.kalman_filter import KalmanFilter2D
from src.settings_manager import SettingsManager
from src.gesture_profiles import GestureProfileManager
from src.analytics import AnalyticsTracker
from src.macro_system import MacroSystem
from src.calibration import UserCalibration
from src.voice_commands import VoiceCommandListener


class VirtualMouse:
    def __init__(self):
        self.settings = SettingsManager("config/settings.json")
        self.profiles = GestureProfileManager("profiles")
        self.profiles.set_active(self.settings.get("active_profile", "default"))
        self.analytics = AnalyticsTracker("analytics")
        self.macros = MacroSystem("macros")
        self.calibration = UserCalibration("default", "calibration")
        self._voice_q: queue.Queue = queue.Queue()
        self.voice = VoiceCommandListener(self._voice_q)

        self.screen_w, self.screen_h = pyautogui.size()

        self._mk_kalman()

        # Runtime state
        self._prev_x = self._prev_y = 0
        self._curr_x = self._curr_y = 0
        self._dragging = False
        self._t_left_click = self._t_right_click = self._t_scroll = 0.0
        self._t_prev_click = 0.0   # for double-click detection
        self._dwell_pos = None
        self._dwell_start = 0.0
        self._last_voice_action = ""
        self.running = True

    # ------------------------------------------------------------------
    # Kalman factory (called on init and after settings change)
    # ------------------------------------------------------------------
    def _mk_kalman(self):
        pn = self.settings.get("kalman_process_noise", 1e-4)
        mn = self.settings.get("kalman_measurement_noise", 0.05)
        self.kf_right = KalmanFilter2D(pn, mn)
        self.kf_left = KalmanFilter2D(pn, mn)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def start(self):
        cam = self.settings.get("camera_index", 0)
        W = self.settings.get("frame_width", 640)
        H = self.settings.get("frame_height", 480)

        cap = cv2.VideoCapture(cam)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

        n_hands = 2 if self.settings.get("dual_hand_enabled", True) else 1
        detector = HandDetector(
            max_hands=n_hands,
            detection_con=self.settings.get("confidence_threshold", 0.7),
            track_con=0.5,
        )

        if self.settings.get("voice_commands_enabled", False):
            self.voice.start()

        p_time = time.time()

        while self.running:
            ok, img = cap.read()
            if not ok:
                print("[Camera] Failed to read frame — check camera_index in settings.")
                break

            img = cv2.flip(img, 1)   # mirror view
            img = detector.find_hands(img, draw=True)
            n = detector.get_hand_count()

            now = time.time()
            fps = 1.0 / max(now - p_time, 1e-6)
            p_time = now
            self.analytics.log_fps(fps)

            self._process_voice()

            fr = self.settings.get("frame_reduction", 100)
            acc = self.settings.get("accessibility_mode", False)
            dwell = self.settings.get("dwell_click_enabled", False)
            dwell_delay = self.settings.get("dwell_click_delay", 1.5)
            scroll_spd = self.settings.get("scroll_speed", 30)
            conf_th = self.settings.get("confidence_threshold", 0.7)

            # ---- Identify which hand index is which physical hand ----
            # Image is flipped → physical right hand = "Left" label from MediaPipe
            # physical left hand = "Right" label from MediaPipe
            dominant = self.settings.get("dominant_hand", "right")
            primary_label = "Left" if dominant == "right" else "Right"
            modifier_label = "Right" if dominant == "right" else "Left"

            primary_idx = self._hand_idx(detector, primary_label, n)
            modifier_idx = self._hand_idx(detector, modifier_label, n)
            # If only one hand and labels don't match, fall back to hand 0
            if primary_idx is None and n == 1:
                primary_idx = 0

            # ---- Primary hand: cursor control ----
            if primary_idx is not None:
                lms, bbox = detector.find_position(img, hand_no=primary_idx, draw=False)
                conf = detector.get_confidence(primary_idx)

                if lms and conf >= conf_th:
                    self.calibration.update(lms, bbox)
                    click_th = self.calibration.get_click_threshold()
                    fingers = detector.fingers_up(primary_idx)

                    zone_r = max(30, fr - 30) if acc else fr
                    self._draw_zone(img, zone_r, W, H)
                    self._draw_conf_bar(img, conf, H)

                    # ── MOVE: index only ──────────────────────────────
                    if fingers[1] == 1 and fingers[2] == 0:
                        x1, y1 = lms[8][1], lms[8][2]
                        tx = np.interp(x1, (zone_r, W - zone_r), (0, self.screen_w))
                        ty = np.interp(y1, (zone_r, H - zone_r), (0, self.screen_h))
                        self._curr_x, self._curr_y = self.kf_right.update(tx, ty)
                        pyautogui.moveTo(self._curr_x, self._curr_y)
                        self.analytics.log_cursor(self._curr_x, self._curr_y)
                        cv2.circle(img, (x1, y1), 9, (0, 255, 100), cv2.FILLED)

                        # Dwell click
                        if dwell:
                            cell = (self._curr_x // 40, self._curr_y // 40)
                            if cell == self._dwell_pos:
                                if time.time() - self._dwell_start > dwell_delay:
                                    pyautogui.click()
                                    self._dwell_start = time.time() + 9999
                                    self.analytics.log_click(self._curr_x, self._curr_y)
                                    self.analytics.log_gesture("dwell_click", conf)
                            else:
                                self._dwell_pos = cell
                                self._dwell_start = time.time()

                    # ── LEFT / DOUBLE CLICK: index + middle close ─────
                    elif fingers[1] == 1 and fingers[2] == 1:
                        length, img, li = detector.find_distance(8, 12, img)
                        if length < click_th and now - self._t_left_click > 0.4:
                            cv2.circle(img, (li[4], li[5]), 13, (0, 255, 0), cv2.FILLED)
                            # Two clicks within 300 ms → double-click
                            if now - self._t_prev_click < 0.30:
                                pyautogui.doubleClick()
                                self._overlay(img, "Double Click!", (50, 100), (166, 227, 161))
                                self.analytics.log_gesture("double_click", conf)
                                self._t_prev_click = 0.0   # reset so next click is single
                            else:
                                pyautogui.click()
                                self.analytics.log_gesture("left_click", conf)
                            self._t_prev_click = self._t_left_click
                            self._t_left_click = now
                            self.analytics.log_click(self._curr_x, self._curr_y)

                    # ── RIGHT CLICK: index + pinky, middle+ring down ──
                    elif fingers[1] == 1 and fingers[4] == 1 and fingers[2] == 0 and fingers[3] == 0:
                        if now - self._t_right_click > 0.6:
                            pyautogui.rightClick()
                            self._t_right_click = now
                            self.analytics.log_gesture("right_click", conf)
                            self._overlay(img, "Right Click", (50, 100), (0, 165, 255))

                    # ── SCROLL: index + middle + ring up ─────────────
                    elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                        if now - self._t_scroll > 0.12:
                            y1 = lms[8][2]
                            direction = 1 if y1 < H // 2 else -1
                            pyautogui.scroll(scroll_spd * direction)
                            self._t_scroll = now
                            label = "Scroll Up" if direction > 0 else "Scroll Down"
                            self.analytics.log_gesture(label.replace(" ", "_").lower(), conf)
                            self._overlay(img, label, (50, 100), (255, 165, 0))

                    # ── DRAG: fist (all fingers down) ─────────────────
                    elif fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                        x1, y1 = lms[8][1], lms[8][2]
                        tx = np.interp(x1, (fr, W - fr), (0, self.screen_w))
                        ty = np.interp(y1, (fr, H - fr), (0, self.screen_h))
                        self._curr_x, self._curr_y = self.kf_right.update(tx, ty)
                        if not self._dragging:
                            pyautogui.mouseDown()
                            self._dragging = True
                            self.analytics.log_gesture("drag", conf)
                        pyautogui.moveTo(self._curr_x, self._curr_y)
                        self._overlay(img, "DRAG", (50, 100), (0, 0, 255))

                    # ── SCREENSHOT: open palm ──────────────────────────
                    elif all(f == 1 for f in fingers):
                        if self.macros.execute("screenshot", cooldown=2.5):
                            self.analytics.log_gesture("screenshot", conf)
                            self._overlay(img, "Screenshot!", (50, 100), (255, 80, 200))

                    else:
                        self._release_drag()
            else:
                self._release_drag()

            # ---- Modifier hand -----------------------------------------------
            dual = self.settings.get("dual_hand_enabled", True)
            if modifier_idx is not None and dual and modifier_idx != primary_idx:
                lms_m, _ = detector.find_position(img, hand_no=modifier_idx, draw=False)
                conf_m = detector.get_confidence(modifier_idx)
                if lms_m and conf_m >= conf_th:
                    fingers_m = detector.fingers_up(modifier_idx)
                    self._handle_modifier(img, fingers_m, conf_m)

            self._draw_hud(img, fps, n)

            cv2.imshow("Virtual Mouse  |  S=Settings  A=Analytics  R=Reset-Cal  Q=Quit", img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                self._open_settings()
            elif key == ord("a"):
                self._open_analytics()
            elif key == ord("r"):
                self.calibration = UserCalibration("default", "calibration")
                print("[Calibration] Reset.")

        cap.release()
        cv2.destroyAllWindows()
        self.voice.stop()
        if self.settings.get("analytics_enabled", True):
            self.analytics.save_session()

    # ------------------------------------------------------------------
    # Modifier hand gestures (physical left hand)
    # ------------------------------------------------------------------
    def _handle_modifier(self, img, fingers, conf):
        # Thumb only → zoom in
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            if self.macros.execute("zoom_in", cooldown=0.7):
                self.analytics.log_gesture("zoom_in", conf)
                self._overlay(img, "Zoom In", (440, 80), (0, 255, 200))

        # Pinky only → zoom out
        elif fingers[4] == 1 and fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
            if self.macros.execute("zoom_out", cooldown=0.7):
                self.analytics.log_gesture("zoom_out", conf)
                self._overlay(img, "Zoom Out", (430, 80), (0, 200, 255))

        # Open palm → switch window
        elif all(f == 1 for f in fingers):
            if self.macros.execute("switch_window", cooldown=1.4):
                self.analytics.log_gesture("switch_window", conf)
                self._overlay(img, "Switch Win", (420, 80), (255, 200, 0))

        # Peace (index + middle) → media play/pause
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0 and fingers[3] == 0 and fingers[4] == 0:
            if self.macros.execute("media_play_pause", cooldown=1.0):
                self.analytics.log_gesture("media_toggle", conf)
                self._overlay(img, "Play/Pause", (420, 80), (200, 100, 255))

        # Fist → screenshot
        elif all(f == 0 for f in fingers):
            if self.macros.execute("screenshot", cooldown=2.0):
                self.analytics.log_gesture("screenshot", conf)
                self._overlay(img, "Screenshot!", (410, 80), (255, 100, 100))

    # ------------------------------------------------------------------
    # Voice command dispatcher
    # ------------------------------------------------------------------
    def _process_voice(self):
        try:
            _, action = self._voice_q.get_nowait()
            self._last_voice_action = action
            if action == "left_click":
                pyautogui.click()
            elif action == "right_click":
                pyautogui.rightClick()
            elif action == "double_click":
                pyautogui.doubleClick()
            elif action == "scroll_up":
                pyautogui.scroll(60)
            elif action == "scroll_down":
                pyautogui.scroll(-60)
            elif action == "stop_voice":
                self.voice.stop()
            elif action in self.macros.macros:
                self.macros.execute(action)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _hand_idx(self, detector, label, n):
        for i in range(n):
            if detector.get_hand_label(i) == label:
                return i
        return None

    def _release_drag(self):
        if self._dragging:
            pyautogui.mouseUp()
            self._dragging = False

    def _draw_zone(self, img, fr, W, H):
        cv2.rectangle(img, (fr, fr), (W - fr, H - fr), (255, 0, 255), 2)

    def _draw_conf_bar(self, img, conf, H):
        bw = int(conf * 120)
        cv2.rectangle(img, (10, H - 28), (130, H - 10), (40, 40, 40), -1)
        c = (0, 255, 0) if conf > 0.8 else (0, 165, 255) if conf > 0.6 else (0, 0, 255)
        cv2.rectangle(img, (10, H - 28), (10 + bw, H - 10), c, -1)
        cv2.putText(img, f"{conf:.0%}", (134, H - 11),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1)

    def _draw_hud(self, img, fps, n):
        cv2.rectangle(img, (0, 0), (210, 70), (0, 0, 0), -1)
        cv2.putText(img, f"FPS: {int(fps)}", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        cv2.putText(img, f"Hands: {n}", (8, 44),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2)
        profile = self.settings.get("active_profile", "default")
        cv2.putText(img, f"Profile: {profile}", (8, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (170, 170, 170), 1)

        h, w = img.shape[:2]
        if self.settings.get("voice_commands_enabled", False):
            cv2.putText(img, "MIC", (w - 55, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 2)
        if self._last_voice_action:
            cv2.putText(img, f"Voice: {self._last_voice_action}", (w - 185, 44),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 200, 255), 1)

    @staticmethod
    def _overlay(img, text, pos, color):
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    def _open_settings(self):
        from gui.settings_gui import SettingsGUI
        SettingsGUI(self.settings, self.profiles, on_change=self._apply_settings).launch()

    def _open_analytics(self):
        from gui.analytics_gui import AnalyticsDashboard
        AnalyticsDashboard(self.analytics).launch()

    def _apply_settings(self, updates):
        self._mk_kalman()
        if updates.get("voice_commands_enabled") and not self.voice.running:
            self.voice.start()
        elif not updates.get("voice_commands_enabled") and self.voice.running:
            self.voice.stop()


# -----------------------------------------------------------------------
# Gesture cheat-sheet printed on startup
# -----------------------------------------------------------------------
CHEAT_SHEET = """
┌─────────────────────────────────────────────────────────┐
│           Virtual Mouse — Gesture Reference              │
├──────────────────────────┬──────────────────────────────┤
│  RIGHT HAND (cursor)     │  LEFT HAND (modifiers)       │
├──────────────────────────┼──────────────────────────────┤
│  ☝  Index only           │  👍 Thumb only  → Zoom In   │
│     → Move cursor        │  🤙 Pinky only  → Zoom Out  │
│  ✌  Index+Middle close   │  ✋ Open palm   → Alt+Tab   │
│     → Left Click         │  ✌  Peace sign  → Play/Pause│
│  ☝🤙 Index+Pinky         │  ✊ Fist        → Screenshot│
│     → Right Click        │                              │
│  🤟 Index+Mid+Ring       │                              │
│     → Scroll (pos-based) │                              │
│  ✊ Fist → Drag          │                              │
│  ✋ Open palm→ Screenshot │                              │
├──────────────────────────┴──────────────────────────────┤
│  S=Settings  A=Analytics  R=Reset calibration  Q=Quit   │
└─────────────────────────────────────────────────────────┘
"""


def main():
    print(CHEAT_SHEET)
    vm = VirtualMouse()
    vm.start()


if __name__ == "__main__":
    main()
