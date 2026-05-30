# Virtual Mouse — Hand Gesture Control

Control your computer with just your hand and a webcam. No mouse required.

Built with OpenCV + MediaPipe + PyAutoGUI.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

> **Legacy mode** (simpler, single-file):  `python "Virtual Mouse.py"`

---

## Gesture Reference

### Right hand — Cursor control

| Gesture | Action |
|---------|--------|
| ☝ Index finger only | Move cursor |
| ✌ Index + Middle (close together) | Left click |
| ☝🤙 Index + Pinky | Right click |
| 🤟 Index + Middle + Ring | Scroll (top half = up, bottom = down) |
| ✊ Fist | Drag mode |
| ✋ Open palm (all 5) | Screenshot |

### Left hand — Modifier shortcuts (dual-hand mode)

| Gesture | Action |
|---------|--------|
| 👍 Thumb only | Zoom In (Ctrl +) |
| 🤙 Pinky only | Zoom Out (Ctrl -) |
| ✋ Open palm | Switch Window (Alt+Tab) |
| ✌ Peace sign | Play / Pause media |
| ✊ Fist | Screenshot |

---

## Features

| Level | Feature | Status |
|-------|---------|--------|
| Core | Cursor movement + left click + scroll + right click + drag | ✅ |
| L1 | **Kalman filter** — eliminates cursor jitter with predictive smoothing | ✅ |
| L1 | **Confidence thresholds** — ignores low-confidence detections | ✅ |
| L1 | **Settings GUI** (Tkinter) — tune sensitivity, smoothing, accessibility | ✅ |
| L1 | **Gesture profiles** — default / gaming / accessibility; save custom JSON | ✅ |
| L2 | **Dual-hand gestures** — right=cursor, left=modifiers | ✅ |
| L2 | **Voice + gesture fusion** — speak "click", "scroll up", "zoom in" etc. | ✅ |
| L2 | **Accessibility mode** — larger zones, dwell-click, slower sensitivity | ✅ |
| L2 | **Adaptive per-user calibration** — learns your hand size over time | ✅ |
| L3 | **Analytics dashboard** — gesture heatmap, click map, FPS, accuracy | ✅ |
| L3 | **Macro/plugin system** — JSON-scripted hotkeys, app launch, screenshots | ✅ |

---

## Keyboard Shortcuts (while running)

| Key | Action |
|-----|--------|
| `S` | Open Settings GUI |
| `A` | Open Analytics dashboard |
| `R` | Reset per-user calibration |
| `Q` | Quit |

---

## Project Structure

```
.
├── main.py                  # Full-featured entry point  ← start here
├── Virtual Mouse.py         # Legacy single-file version
├── HandTracking.py          # Legacy hand tracking module
├── requirements.txt
│
├── src/
│   ├── hand_tracking.py     # HandDetector — upgraded MediaPipe wrapper
│   ├── kalman_filter.py     # KalmanFilter2D — smooth cursor tracking
│   ├── settings_manager.py  # JSON settings with live reload
│   ├── gesture_profiles.py  # Profile manager (default/gaming/accessibility)
│   ├── voice_commands.py    # Background speech recognition thread
│   ├── analytics.py         # Session gesture/click/FPS logging
│   ├── macro_system.py      # JSON-defined hotkey & screenshot macros
│   └── calibration.py       # Adaptive hand-scale learning per user
│
├── gui/
│   ├── settings_gui.py      # Tkinter settings panel
│   └── analytics_gui.py     # Matplotlib analytics dashboard
│
├── profiles/                # Gesture profile JSON files (auto-created)
├── macros/                  # Macro definition JSON files (auto-created)
├── config/                  # settings.json (auto-created)
├── analytics/               # Per-session analytics logs (auto-created)
├── calibration/             # Per-user calibration data (auto-created)
└── screenshots/             # Screenshots taken by gesture (auto-created)
```

---

## Custom Gesture Profiles

Edit or create a file in `profiles/` (e.g. `profiles/my_profile.json`):

```json
{
  "name": "my_profile",
  "description": "My custom mapping",
  "gestures": {
    "move":       { "fingers": [0,1,0,0,0], "action": "move_cursor" },
    "left_click": { "fingers": [0,1,1,0,0], "action": "left_click" },
    "scroll":     { "fingers": [0,1,1,1,0], "action": "scroll" }
  },
  "left_hand_gestures": {}
}
```

`fingers` array = `[thumb, index, middle, ring, pinky]` where `1` = up, `0` = down.

---

## Custom Macros

Add entries to `macros/user_macros.json`:

```json
{
  "open_browser": {
    "steps": [
      { "type": "launch", "command": "xdg-open https://google.com" }
    ]
  },
  "type_hello": {
    "steps": [
      { "type": "type", "text": "Hello, World!" }
    ]
  }
}
```

Step types: `hotkey`, `key`, `type`, `double_click`, `screenshot`, `launch`, `delay`.

---

## Voice Commands

Enable in Settings (`S` key) or `config/settings.json`:

```json
{ "voice_commands_enabled": true }
```

Supported phrases: *click, left click, right click, double click, scroll up, scroll down, screenshot, zoom in, zoom out, switch window, select all, copy, paste, undo, play, pause, stop listening*

Requires: `pip install SpeechRecognition pyaudio`

---

## Dependencies

```
opencv-python   mediapipe   numpy   pyautogui   Pillow
matplotlib      SpeechRecognition   pyaudio (optional)
```

---

## Tips

- **Jitter?** Lower `kalman_measurement_noise` in Settings (smoother but more lag).
- **Accidental clicks?** Increase `click_distance_threshold`.
- **Too slow?** Reduce `frame_reduction` (smaller border zone).
- **Left-handed?** Set `dominant_hand = left` in Settings.
- **Analytics not showing?** Install matplotlib: `pip install matplotlib`.

---

## Author

[adityaraj9900](https://github.com/adityaraj9900)
