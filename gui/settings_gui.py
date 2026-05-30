import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings_manager import SettingsManager, DEFAULT_SETTINGS
from src.gesture_profiles import GestureProfileManager

BG = "#1e1e2e"
FG = "#cdd6f4"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
SURFACE = "#313244"


class SettingsGUI:
    def __init__(self, settings: SettingsManager, profiles: GestureProfileManager,
                 on_change=None):
        self.settings = settings
        self.profiles = profiles
        self.on_change = on_change

    def launch(self, blocking=False):
        if blocking:
            self._build()
        else:
            threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        root = tk.Tk()
        root.title("Virtual Mouse — Settings")
        root.geometry("500x660")
        root.resizable(False, False)
        root.configure(bg=BG)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TLabel", background=BG, foreground=FG, font=("Helvetica", 10))
        style.configure("TFrame", background=BG)
        style.configure("TCheckbutton", background=BG, foreground=FG, font=("Helvetica", 10))
        style.configure("TCombobox", fieldbackground=SURFACE, foreground=FG)
        style.configure("TScale", background=BG, troughcolor=SURFACE)

        # Header
        tk.Label(root, text="Virtual Mouse Settings", bg=BG, fg=ACCENT,
                 font=("Helvetica", 15, "bold")).pack(pady=(16, 4))
        tk.Frame(root, bg=SURFACE, height=1).pack(fill=tk.X, padx=20)

        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        vars_ = {}

        def section(title):
            tk.Label(frame, text=title, bg=BG, fg=GREEN,
                     font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(12, 1))
            tk.Frame(frame, bg=SURFACE, height=1).pack(fill=tk.X, pady=2)

        def slider(label, key, lo, hi, scale=1):
            raw = self.settings.get(key, DEFAULT_SETTINGS.get(key, lo))
            init = int(float(raw) * scale)
            v = tk.IntVar(value=init)
            vars_[key] = (v, scale)
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=label, width=36).pack(side=tk.LEFT)
            lbl = tk.Label(row, textvariable=v, bg=BG, fg=YELLOW, width=4)
            lbl.pack(side=tk.RIGHT)
            ttk.Scale(row, from_=lo, to=hi, variable=v, orient=tk.HORIZONTAL).pack(
                side=tk.RIGHT, fill=tk.X, expand=True, padx=4)

        def check(label, key):
            v = tk.BooleanVar(value=self.settings.get(key, False))
            vars_[key] = (v, None)
            ttk.Checkbutton(frame, text=label, variable=v).pack(anchor=tk.W, pady=2)

        # Profile
        section("Gesture Profile")
        profile_frame = ttk.Frame(frame)
        profile_frame.pack(fill=tk.X, pady=4)
        ttk.Label(profile_frame, text="Active Profile:").pack(side=tk.LEFT)
        pv = tk.StringVar(value=self.settings.get("active_profile", "default"))
        vars_["active_profile"] = (pv, None)
        ttk.Combobox(profile_frame, textvariable=pv,
                     values=self.profiles.list_profiles(),
                     state="readonly", width=14).pack(side=tk.LEFT, padx=8)

        # Dominant hand
        ttk.Label(profile_frame, text="  Hand:").pack(side=tk.LEFT)
        hv = tk.StringVar(value=self.settings.get("dominant_hand", "right"))
        vars_["dominant_hand"] = (hv, None)
        ttk.Combobox(profile_frame, textvariable=hv, values=["right", "left"],
                     state="readonly", width=7).pack(side=tk.LEFT, padx=4)

        # Cursor
        section("Cursor Control")
        slider("Frame border zone (px):", "frame_reduction", 40, 200)
        slider("Kalman noise ×100 (lower=smoother):", "kalman_measurement_noise", 1, 50, scale=100)

        # Gestures
        section("Gesture Thresholds")
        slider("Click distance (px):", "click_distance_threshold", 15, 80)
        slider("Scroll speed:", "scroll_speed", 5, 120)

        # Features
        section("Features")
        check("Voice Commands (requires SpeechRecognition + pyaudio)", "voice_commands_enabled")
        check("Dual-Hand Gestures (right=cursor, left=modifiers)", "dual_hand_enabled")
        check("Analytics Tracking", "analytics_enabled")

        # Accessibility
        section("Accessibility Mode")
        check("Accessibility Mode (larger zones, slower sensitivity)", "accessibility_mode")
        check("Dwell Click (hover in place to click)", "dwell_click_enabled")
        slider("Dwell click delay ×10 (= seconds):", "dwell_click_delay", 5, 40, scale=10)

        # Camera
        section("Camera")
        slider("Camera index (0=default):", "camera_index", 0, 4)

        # Buttons
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=12)

        def save():
            updates = {}
            for key, (var, scale) in vars_.items():
                val = var.get()
                if scale and scale != 1:
                    val = val / scale
                updates[key] = val
            self.settings.update(updates)
            self.profiles.set_active(updates.get("active_profile", "default"))
            if self.on_change:
                self.on_change(updates)
            messagebox.showinfo("Settings", "Saved & applied!")

        def reset():
            self.settings.settings = DEFAULT_SETTINGS.copy()
            self.settings.save()
            messagebox.showinfo("Settings", "Reset to defaults. Restart to fully apply.")

        tk.Button(btn_frame, text="Save & Apply", command=save,
                  bg=ACCENT, fg=BG, font=("Helvetica", 10, "bold"),
                  relief=tk.FLAT, padx=18, pady=7).pack(side=tk.LEFT, padx=8)

        tk.Button(btn_frame, text="Reset Defaults", command=reset,
                  bg=RED, fg=BG, font=("Helvetica", 10),
                  relief=tk.FLAT, padx=18, pady=7).pack(side=tk.LEFT, padx=8)

        root.mainloop()
