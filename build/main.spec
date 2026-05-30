# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Virtual Mouse.

Build with:
    cd build
    pyinstaller main.spec

Output:
    dist/VirtualMouse          (Linux)
    dist/VirtualMouse.exe      (Windows)
    dist/VirtualMouse.app      (macOS)
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

ROOT = os.path.abspath("..")

# ── Data files ────────────────────────────────────────────────────────────────
mediapipe_datas = collect_data_files("mediapipe")
try:
    cv2_datas = collect_data_files("cv2")
except Exception:
    cv2_datas = []

app_datas = [
    (os.path.join(ROOT, "src"),      "src"),
    (os.path.join(ROOT, "gui"),      "gui"),
    (os.path.join(ROOT, "profiles"), "profiles"),
    (os.path.join(ROOT, "macros"),   "macros"),
] + mediapipe_datas + cv2_datas

# ── Hidden imports ─────────────────────────────────────────────────────────────
hidden = [
    # OpenCV
    "cv2",
    # MediaPipe
    "mediapipe",
    "mediapipe.python._framework_bindings",
    "mediapipe.python.solutions.hands",
    "mediapipe.python.solutions.drawing_utils",
    "mediapipe.python.solutions.drawing_styles",
    # Protobuf
    "google.protobuf",
    "google.protobuf.descriptor",
    "google.protobuf.descriptor_pool",
    "google.protobuf.reflection",
    "google.protobuf.symbol_database",
    # PyAutoGUI
    "pyautogui",
    "pyscreeze",
    "pygetwindow",
    # GUI
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    # Analytics
    "matplotlib",
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends._backend_tk",
    # Imaging
    "PIL",
    "PIL.Image",
    "PIL.ImageGrab",
    # Numerics
    "numpy",
    "numpy.core._multiarray_umath",
    # Speech (optional — bundled so the toggle works without reinstall)
    "speech_recognition",
    # Project modules
    "src.hand_tracking",
    "src.kalman_filter",
    "src.settings_manager",
    "src.gesture_profiles",
    "src.analytics",
    "src.macro_system",
    "src.calibration",
    "src.voice_commands",
    "gui.settings_gui",
    "gui.analytics_gui",
]

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=collect_dynamic_libs("mediapipe"),
    datas=app_datas,
    hiddenimports=hidden,
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["test", "tests", "unittest", "doctest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Platform-specific output ──────────────────────────────────────────────────

_icon_icns = os.path.join(ROOT, "assets", "icon.icns")
_icon_ico  = os.path.join(ROOT, "assets", "icon.ico")
_icon_png  = os.path.join(ROOT, "assets", "icon.png")

if sys.platform == "darwin":
    # ── macOS: .app bundle ──────────────────────────────────────────────────
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name="VirtualMouse",
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon=_icon_icns if os.path.exists(_icon_icns) else None,
    )
    coll = COLLECT(
        exe, a.binaries, a.zipfiles, a.datas,
        strip=False, upx=True, upx_exclude=[],
        name="VirtualMouse",
    )
    app = BUNDLE(
        coll,
        name="VirtualMouse.app",
        icon=_icon_icns if os.path.exists(_icon_icns) else None,
        bundle_identifier="com.virtualMouse.handGesture",
        info_plist={
            "CFBundleName": "Virtual Mouse",
            "CFBundleDisplayName": "Virtual Mouse",
            "CFBundleVersion": "2.0.0",
            "CFBundleShortVersionString": "2.0.0",
            "NSCameraUsageDescription":
                "Virtual Mouse uses your camera to detect hand gestures for cursor control.",
            "NSMicrophoneUsageDescription":
                "Virtual Mouse uses the microphone for optional voice commands.",
            "LSUIElement": False,
            "NSHighResolutionCapable": True,
        },
    )

elif sys.platform == "win32":
    # ── Windows: single .exe ────────────────────────────────────────────────
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name="VirtualMouse",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        icon=_icon_ico if os.path.exists(_icon_ico) else None,
        version_file=None,
        uac_admin=False,
    )

else:
    # ── Linux: single binary ────────────────────────────────────────────────
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name="VirtualMouse",
        debug=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon=_icon_png if os.path.exists(_icon_png) else None,
    )
