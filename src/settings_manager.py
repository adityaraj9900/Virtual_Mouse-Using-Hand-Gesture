import json
import os

DEFAULT_SETTINGS = {
    "camera_index": 0,
    "frame_width": 640,
    "frame_height": 480,
    "frame_reduction": 100,
    "kalman_process_noise": 1e-4,
    "kalman_measurement_noise": 0.05,
    "click_distance_threshold": 40,
    "confidence_threshold": 0.7,
    "scroll_speed": 30,
    "voice_commands_enabled": False,
    "accessibility_mode": False,
    "dwell_click_enabled": False,
    "dwell_click_delay": 1.5,
    "dual_hand_enabled": True,
    "analytics_enabled": True,
    "active_profile": "default",
    "dominant_hand": "right",
}


class SettingsManager:
    def __init__(self, settings_file="config/settings.json"):
        self.settings_file = settings_file
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file) as f:
                    self.settings.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.settings_file) or ".", exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key, default=None):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key, default))

    def set(self, key, value):
        self.settings[key] = value

    def update(self, updates: dict):
        self.settings.update(updates)
        self.save()
