import cv2
import mediapipe as mp
import math


class HandDetector:
    def __init__(self, mode=False, max_hands=2, detection_con=0.8, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]
        self.results = None
        self.lm_list = []

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0, draw=True):
        x_list, y_list = [], []
        bbox = []
        self.lm_list = []

        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, _ = img.shape
                for id, lm in enumerate(my_hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    x_list.append(cx)
                    y_list.append(cy)
                    self.lm_list.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                xmin, xmax = min(x_list), max(x_list)
                ymin, ymax = min(y_list), max(y_list)
                bbox = (xmin, ymin, xmax, ymax)

                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)

        return self.lm_list, bbox

    def fingers_up(self, hand_no=0):
        fingers = []
        if not self.lm_list:
            return fingers

        is_right_label = True
        if self.results and self.results.multi_handedness:
            if hand_no < len(self.results.multi_handedness):
                label = self.results.multi_handedness[hand_no].classification[0].label
                is_right_label = label == "Right"

        # Thumb — direction depends on handedness label
        tip, joint = self.lm_list[self.tip_ids[0]][1], self.lm_list[self.tip_ids[0] - 1][1]
        fingers.append(1 if (tip > joint) == is_right_label else 0)

        # Other four fingers — tip y above lower-joint y = finger up
        for id in range(1, 5):
            fingers.append(
                1 if self.lm_list[self.tip_ids[id]][2] < self.lm_list[self.tip_ids[id] - 2][2] else 0
            )
        return fingers

    def find_distance(self, p1, p2, img, draw=True, r=15, t=3):
        if not self.lm_list or p1 >= len(self.lm_list) or p2 >= len(self.lm_list):
            return 0, img, []

        x1, y1 = self.lm_list[p1][1:]
        x2, y2 = self.lm_list[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        return math.hypot(x2 - x1, y2 - y1), img, [x1, y1, x2, y2, cx, cy]

    def get_hand_count(self):
        if self.results and self.results.multi_hand_landmarks:
            return len(self.results.multi_hand_landmarks)
        return 0

    def get_hand_label(self, hand_no=0):
        if self.results and self.results.multi_handedness:
            if hand_no < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_no].classification[0].label
        return None

    def get_confidence(self, hand_no=0):
        if self.results and self.results.multi_handedness:
            if hand_no < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_no].classification[0].score
        return 0.0
