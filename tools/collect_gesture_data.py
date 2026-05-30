"""
Gesture Data Collector
======================
Records hand landmark CSVs for training a custom gesture classifier.

Usage:
    python tools/collect_gesture_data.py --gesture thumbs_up --samples 200
    python tools/collect_gesture_data.py --gesture peace_sign --samples 200
    python tools/collect_gesture_data.py --gesture point_gun  --samples 200

Each run appends rows to  tools/gesture_data/<gesture_name>.csv
Each row = 63 values: x0,y0,z0, x1,y1,z1, ... x20,y20,z20
(21 landmarks × 3 coords, all normalised to wrist position)

After collecting ≥ 3 gestures run:
    python tools/train_gesture_model.py
"""

import argparse
import csv
import os
import sys
import time

import cv2
import mediapipe as mp
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "gesture_data")
os.makedirs(DATA_DIR, exist_ok=True)

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils


def normalise(landmarks):
    """Flatten & normalise landmarks relative to wrist (landmark 0)."""
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
    pts -= pts[0]                          # translate to wrist origin
    scale = np.max(np.abs(pts)) or 1.0    # scale to [-1, 1]
    pts /= scale
    return pts.flatten().tolist()


def collect(gesture_name: str, n_samples: int, camera_idx: int):
    out_file = os.path.join(DATA_DIR, f"{gesture_name}.csv")
    existing = 0
    if os.path.exists(out_file):
        with open(out_file) as f:
            existing = sum(1 for _ in f)
    print(f"\n[Collector] Gesture : {gesture_name}")
    print(f"[Collector] Target  : {n_samples} new samples  (existing: {existing})")
    print(f"[Collector] Output  : {out_file}")
    print("\nPress  SPACE  to start recording,  Q  to quit early.\n")

    cap = cv2.VideoCapture(camera_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    collected = 0
    recording = False
    countdown = 0

    with open(out_file, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        while collected < n_samples:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res   = hands.process(rgb)

            status_color = (0, 255, 0) if recording else (0, 165, 255)
            cv2.rectangle(frame, (0, 0), (640, 480), status_color, 3)

            if res.multi_hand_landmarks:
                lms = res.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, lms, mp_hands.HAND_CONNECTIONS)

                if recording and countdown == 0:
                    row = normalise(lms.landmark)
                    writer.writerow(row)
                    collected += 1

            # HUD
            mode  = "RECORDING" if recording else "READY (SPACE to start)"
            prog  = f"{collected}/{n_samples}"
            cv2.putText(frame, f"Gesture: {gesture_name}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Samples: {prog}", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 255, 200), 2)
            cv2.putText(frame, mode, (10, 86),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

            if countdown > 0:
                cv2.putText(frame, str(countdown), (300, 260),
                            cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 255), 8)

            cv2.imshow("Gesture Collector — Q to quit", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            elif key == ord(" ") and not recording:
                recording = True

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[Collector] Saved {collected} samples for '{gesture_name}' → {out_file}")
    total = existing + collected
    print(f"[Collector] Total in file: {total} rows")


def main():
    parser = argparse.ArgumentParser(description="Collect gesture landmark data")
    parser.add_argument("--gesture", required=True, help="Gesture label (no spaces)")
    parser.add_argument("--samples", type=int, default=200, help="Number of samples to collect")
    parser.add_argument("--camera",  type=int, default=0,   help="Camera index")
    args = parser.parse_args()

    if " " in args.gesture:
        sys.exit("Gesture name must not contain spaces — use underscores.")

    collect(args.gesture, args.samples, args.camera)


if __name__ == "__main__":
    main()
