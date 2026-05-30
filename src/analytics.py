import json
import os
import time
from collections import defaultdict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AnalyticsTracker:
    def __init__(self, log_dir="analytics"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        self.session_start = time.time()
        self.gesture_counts = defaultdict(int)
        self.click_positions = []
        self.cursor_positions = []
        self.fps_samples = []
        self.confidence_samples = []
        self._cursor_sample_counter = 0

        self.session_file = os.path.join(log_dir, f"session_{int(self.session_start)}.json")

    def log_gesture(self, name: str, confidence: float = 1.0):
        self.gesture_counts[name] += 1
        self.confidence_samples.append(confidence)

    def log_click(self, x: int, y: int, click_type: str = "left"):
        self.click_positions.append({
            "x": x, "y": y,
            "type": click_type,
            "t": round(time.time() - self.session_start, 2),
        })

    def log_cursor(self, x: int, y: int):
        self._cursor_sample_counter += 1
        if self._cursor_sample_counter % 8 == 0:
            self.cursor_positions.append({"x": x, "y": y})

    def log_fps(self, fps: float):
        self.fps_samples.append(fps)

    def _mean(self, lst):
        if not lst:
            return 0.0
        if NUMPY_AVAILABLE:
            import numpy as np
            return float(np.mean(lst))
        return sum(lst) / len(lst)

    def get_session_stats(self):
        return {
            "duration_seconds": round(time.time() - self.session_start, 1),
            "total_gestures": sum(self.gesture_counts.values()),
            "gesture_breakdown": dict(self.gesture_counts),
            "total_clicks": len(self.click_positions),
            "average_fps": round(self._mean(self.fps_samples), 1),
            "average_confidence": round(self._mean(self.confidence_samples), 3),
        }

    def save_session(self):
        data = self.get_session_stats()
        data["click_positions"] = self.click_positions[-300:]
        data["cursor_heatmap"] = self.cursor_positions[-600:]
        with open(self.session_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Analytics] Session saved → {self.session_file}")

    def load_all_sessions(self):
        sessions = []
        for fname in sorted(os.listdir(self.log_dir)):
            if fname.startswith("session_") and fname.endswith(".json"):
                with open(os.path.join(self.log_dir, fname)) as f:
                    sessions.append(json.load(f))
        return sessions
