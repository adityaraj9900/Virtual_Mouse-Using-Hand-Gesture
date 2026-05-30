import json
import os
import time
import subprocess

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

DEFAULT_MACROS = {
    "zoom_in":         {"steps": [{"type": "hotkey", "keys": ["ctrl", "+"]}]},
    "zoom_out":        {"steps": [{"type": "hotkey", "keys": ["ctrl", "-"]}]},
    "switch_window":   {"steps": [{"type": "hotkey", "keys": ["alt", "tab"]}]},
    "select_all":      {"steps": [{"type": "hotkey", "keys": ["ctrl", "a"]}]},
    "copy":            {"steps": [{"type": "hotkey", "keys": ["ctrl", "c"]}]},
    "paste":           {"steps": [{"type": "hotkey", "keys": ["ctrl", "v"]}]},
    "undo":            {"steps": [{"type": "hotkey", "keys": ["ctrl", "z"]}]},
    "media_play_pause":{"steps": [{"type": "key", "key": "playpause"}]},
    "double_click":    {"steps": [{"type": "double_click"}]},
    "screenshot": {
        "steps": [{"type": "screenshot", "save_path": "screenshots/"}],
    },
}


class MacroSystem:
    def __init__(self, macros_dir="macros"):
        self.macros_dir = macros_dir
        self.macros = {}
        os.makedirs(macros_dir, exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        self._seed_defaults()
        self.load_all()
        self._cooldowns: dict = {}

    def _seed_defaults(self):
        path = os.path.join(self.macros_dir, "default_macros.json")
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(DEFAULT_MACROS, f, indent=2)

    def load_all(self):
        for fname in os.listdir(self.macros_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.macros_dir, fname)) as f:
                    self.macros.update(json.load(f))

    def execute(self, name: str, cooldown: float = 0.5) -> bool:
        if not PYAUTOGUI_AVAILABLE:
            return False
        now = time.time()
        if now - self._cooldowns.get(name, 0) < cooldown:
            return False
        macro = self.macros.get(name)
        if not macro:
            return False
        self._cooldowns[name] = now
        for step in macro.get("steps", []):
            t = step.get("type")
            if t == "hotkey":
                pyautogui.hotkey(*step["keys"])
            elif t == "key":
                pyautogui.press(step["key"])
            elif t == "type":
                pyautogui.write(step["text"], interval=0.04)
            elif t == "double_click":
                pyautogui.doubleClick()
            elif t == "screenshot":
                save_dir = step.get("save_path", "screenshots/")
                os.makedirs(save_dir, exist_ok=True)
                fname = os.path.join(save_dir, f"shot_{int(time.time())}.png")
                pyautogui.screenshot().save(fname)
                print(f"[Macro] Screenshot saved: {fname}")
            elif t == "launch":
                subprocess.Popen(step["command"], shell=True)
            elif t == "delay":
                time.sleep(step.get("seconds", 0.1))
        return True

    def add_macro(self, name: str, steps: list):
        self.macros[name] = {"steps": steps}
        path = os.path.join(self.macros_dir, "user_macros.json")
        user = {}
        if os.path.exists(path):
            with open(path) as f:
                user = json.load(f)
        user[name] = self.macros[name]
        with open(path, "w") as f:
            json.dump(user, f, indent=2)
