"""
HandTracking.py — Legacy module kept for backwards compatibility.
For new projects use src/hand_tracking.py (HandDetector class).
"""

import cv2
import mediapipe as mp
import time
import math
import numpy as np


class handDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.8, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = float(detectionCon) if detectionCon else 0.8
        self.trackCon = float(trackCon)

        self.mpHands = mp.solutions.hands
        # Fixed: use keyword args — positional args deprecated in mediapipe ≥0.9
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon,
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]
        self.results = None
        self.lmList = []

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList, yList, bbox = [], [], []
        self.lmList = []
        if self.results and self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                h, w, _ = img.shape
                for id, lm in enumerate(myHand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    xList.append(cx)
                    yList.append(cy)
                    self.lmList.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = xmin, ymin, xmax, ymax
                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                                  (0, 255, 0), 2)
        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        if not self.lmList:
            return fingers
        # Thumb
        fingers.append(1 if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1] else 0)
        # Other fingers
        for id in range(1, 5):
            fingers.append(
                1 if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2] else 0
            )
        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        if not self.lmList or p1 >= len(self.lmList) or p2 >= len(self.lmList):
            return 0, img, []
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        return math.hypot(x2 - x1, y2 - y1), img, [x1, y1, x2, y2, cx, cy]


def main():
    pTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if lmList:
            print(lmList[4])
        cTime = time.time()
        fps = 1 / max(cTime - pTime, 1e-6)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    main()
