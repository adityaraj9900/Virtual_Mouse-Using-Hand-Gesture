import json
import os
from typing import Dict, Any

# fingers list: [thumb, index, middle, ring, pinky]
DEFAULT_PROFILE = {
    "name": "default",
    "description": "Balanced default mapping — works for most users",
    "gestures": {
        "move":        {"fingers": [0, 1, 0, 0, 0], "action": "move_cursor"},
        "left_click":  {"fingers": [0, 1, 1, 0, 0], "action": "left_click"},
        "right_click": {"fingers": [0, 1, 0, 0, 1], "action": "right_click"},
        "scroll":      {"fingers": [0, 1, 1, 1, 0], "action": "scroll"},
        "drag":        {"fingers": [0, 0, 0, 0, 0], "action": "drag"},
        "screenshot":  {"fingers": [1, 1, 1, 1, 1], "action": "screenshot"},
    },
    "left_hand_gestures": {
        "zoom_in":       {"fingers": [1, 0, 0, 0, 0], "action": "zoom_in"},
        "zoom_out":      {"fingers": [0, 0, 0, 0, 1], "action": "zoom_out"},
        "switch_window": {"fingers": [1, 1, 1, 1, 1], "action": "switch_window"},
        "media_toggle":  {"fingers": [0, 1, 1, 0, 0], "action": "media_play_pause"},
        "screenshot":    {"fingers": [0, 0, 0, 0, 0], "action": "screenshot"},
    },
}

GAMING_PROFILE = {
    "name": "gaming",
    "description": "Tighter click threshold, no drag — fast reaction gestures",
    "gestures": {
        "move":        {"fingers": [0, 1, 0, 0, 0], "action": "move_cursor"},
        "left_click":  {"fingers": [0, 1, 1, 0, 0], "action": "left_click"},
        "right_click": {"fingers": [1, 1, 0, 0, 0], "action": "right_click"},
        "scroll":      {"fingers": [0, 1, 1, 1, 0], "action": "scroll"},
    },
    "left_hand_gestures": {},
}

ACCESSIBILITY_PROFILE = {
    "name": "accessibility",
    "description": "Larger zones, dwell-click, slow sensitivity for motor-impaired users",
    "gestures": {
        "move":        {"fingers": [0, 1, 0, 0, 0], "action": "move_cursor"},
        "dwell_click": {"fingers": [0, 1, 1, 0, 0], "action": "dwell_click"},
        "right_click": {"fingers": [0, 1, 0, 0, 1], "action": "right_click"},
        "scroll":      {"fingers": [0, 1, 1, 1, 0], "action": "scroll"},
    },
    "left_hand_gestures": {},
}


class GestureProfileManager:
    def __init__(self, profiles_dir="profiles"):
        self.profiles_dir = profiles_dir
        self.profiles: Dict[str, Any] = {}
        self.active_profile = "default"
        os.makedirs(profiles_dir, exist_ok=True)
        self._seed_defaults()
        self.load_all()

    def _seed_defaults(self):
        for profile in [DEFAULT_PROFILE, GAMING_PROFILE, ACCESSIBILITY_PROFILE]:
            path = os.path.join(self.profiles_dir, f"{profile['name']}.json")
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump(profile, f, indent=2)

    def load_all(self):
        for fname in os.listdir(self.profiles_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.profiles_dir, fname)) as f:
                    p = json.load(f)
                    self.profiles[p["name"]] = p

    def get_profile(self, name=None):
        return self.profiles.get(name or self.active_profile, DEFAULT_PROFILE)

    def set_active(self, name):
        if name in self.profiles:
            self.active_profile = name
            return True
        return False

    def save_profile(self, profile: dict):
        self.profiles[profile["name"]] = profile
        path = os.path.join(self.profiles_dir, f"{profile['name']}.json")
        with open(path, "w") as f:
            json.dump(profile, f, indent=2)

    def list_profiles(self):
        return list(self.profiles.keys())
