# Contributing to Virtual Mouse

Thanks for your interest in contributing! Here's everything you need to get started.

---

## Project structure

```
src/          Core modules (hand tracking, Kalman filter, settings, etc.)
gui/          Tkinter GUIs (settings panel, analytics dashboard)
tools/        ML data collection and model training scripts
build/        PyInstaller packaging
docs/         Browser demo (GitHub Pages)
profiles/     Bundled gesture profiles (JSON)
macros/       Bundled macros (JSON)
```

---

## Setup

```bash
git clone https://github.com/adityaraj9900/Virtual_Mouse-Using-Hand-Gesture.git
cd Virtual_Mouse-Using-Hand-Gesture
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running locally

```bash
python main.py          # full-featured app
python "Virtual Mouse.py"  # legacy single-file version
```

---

## Ways to contribute

### Bug fixes
Open an issue first describing the bug and repro steps, then submit a PR.

### New gesture profiles
Add a JSON file to `profiles/` following the schema in `profiles/default.json`.
Name it descriptively (e.g. `profiles/presentation.json`).

### New macros
Add entries to `macros/default_macros.json` or create a new JSON file in `macros/`.
Macro step types: `hotkey`, `key`, `type`, `double_click`, `screenshot`, `launch`, `delay`.

### New features
For anything beyond a small fix, please open an issue or discussion first to
align on the design before investing time in a PR.

---

## Pull request checklist

- [ ] `python -m py_compile <changed files>` passes (no syntax errors)
- [ ] Tested on webcam with at least one gesture
- [ ] No new `print()` statements in `src/` (use the existing logging pattern)
- [ ] Settings that affect behaviour are exposed in `src/settings_manager.py → DEFAULT_SETTINGS`
- [ ] New dependencies added to `requirements.txt` **and** `pyproject.toml`

---

## Code style

- Python 3.9+ compatible
- Snake_case everywhere; class names PascalCase
- No type annotations required, but welcome
- Max line length ~100 chars (soft limit)
- No docstrings on obvious methods; add a one-line comment only when the *why* is non-obvious

---

## Reporting issues

Please include:
- OS and Python version
- `pip list` output (or at minimum `mediapipe`, `opencv-python`, `pyautogui` versions)
- Whether you are running `python main.py` or the packaged installer
- Steps to reproduce + error traceback if applicable
