import json
import os
from collections import deque

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class UserCalibration:
    """Learns a user's hand size over time and adapts click/gesture thresholds."""

    BASE_CLICK_DISTANCE = 40
    BASE_HAND_SPAN = 150.0  # pixels at reference distance

    def __init__(self, user_id="default", calibration_dir="calibration"):
        self.user_id = user_id
        self.cal_file = os.path.join(calibration_dir, f"{user_id}.json")
        os.makedirs(calibration_dir, exist_ok=True)

        self.hand_scale = 1.0
        self.click_threshold = self.BASE_CLICK_DISTANCE

        self._span_buf = deque(maxlen=120)
        self._updates = 0

        self._load()

    def update(self, lm_list: list, bbox: tuple):
        if not lm_list or not bbox:
            return
        xmin, ymin, xmax, ymax = bbox
        span = max(xmax - xmin, ymax - ymin)
        if span > 20:
            self._span_buf.append(span)
            self._updates += 1
            if self._updates % 60 == 0:
                self._adapt()

    def _adapt(self):
        if len(self._span_buf) < 30:
            return
        if NUMPY_AVAILABLE:
            import numpy as np
            median = float(np.median(self._span_buf))
        else:
            sorted_buf = sorted(self._span_buf)
            median = sorted_buf[len(sorted_buf) // 2]

        self.hand_scale = median / self.BASE_HAND_SPAN
        self.click_threshold = max(25, min(65, int(self.BASE_CLICK_DISTANCE * self.hand_scale)))
        self._save()

    def get_click_threshold(self) -> int:
        return self.click_threshold

    def _load(self):
        if os.path.exists(self.cal_file):
            try:
                with open(self.cal_file) as f:
                    data = json.load(f)
                self.hand_scale = data.get("hand_scale", 1.0)
                self.click_threshold = data.get("click_threshold", self.BASE_CLICK_DISTANCE)
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        with open(self.cal_file, "w") as f:
            json.dump({
                "user_id": self.user_id,
                "hand_scale": round(self.hand_scale, 4),
                "click_threshold": self.click_threshold,
            }, f, indent=2)
