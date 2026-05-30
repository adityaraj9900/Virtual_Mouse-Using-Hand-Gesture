#!/usr/bin/env python3
"""
Cross-platform build script for Virtual Mouse installer.

Usage:
    python build/build.py             # auto-detect platform
    python build/build.py --clean     # clean dist/ and build/ first
    python build/build.py --dmg       # macOS: also package into .dmg
    python build/build.py --zip       # Windows/Linux: zip the output

Requirements:
    pip install pyinstaller
    (optional) brew install create-dmg   # for --dmg on macOS
"""

import sys
import os
import shutil
import subprocess
import argparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT, "build")
DIST_DIR = os.path.join(ROOT, "dist")
WORK_DIR = os.path.join(ROOT, "build", "_pyinstaller_work")


def run(cmd: list, cwd=ROOT):
    print(f"\n▶ {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(f"❌ Command failed with code {result.returncode}")


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        sys.exit("❌ PyInstaller not found. Install it:\n   pip install pyinstaller")


def clean():
    for d in [DIST_DIR, WORK_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"🗑  Removed {d}")


def build():
    spec = os.path.join(BUILD_DIR, "main.spec")
    run([
        sys.executable, "-m", "PyInstaller",
        "--distpath", DIST_DIR,
        "--workpath", WORK_DIR,
        "--noconfirm",
        spec,
    ])


def package_dmg():
    """macOS only: wrap VirtualMouse.app in a .dmg with create-dmg."""
    app = os.path.join(DIST_DIR, "VirtualMouse.app")
    dmg = os.path.join(DIST_DIR, "VirtualMouse.dmg")

    if not os.path.exists(app):
        sys.exit(f"❌ {app} not found — run build first")

    if shutil.which("create-dmg"):
        run([
            "create-dmg",
            "--volname", "Virtual Mouse",
            "--window-size", "600", "400",
            "--icon-size", "100",
            "--icon", "VirtualMouse.app", "175", "190",
            "--app-drop-link", "425", "190",
            "--no-internet-enable",
            dmg,
            app,
        ])
        print(f"\n✅ DMG created: {dmg}")
    else:
        # Fallback: hdiutil
        run([
            "hdiutil", "create",
            "-volname", "VirtualMouse",
            "-srcfolder", app,
            "-ov", "-format", "UDZO",
            dmg,
        ])
        print(f"\n✅ DMG created (hdiutil): {dmg}")


def package_zip():
    name = "VirtualMouse"
    src = os.path.join(DIST_DIR, name)
    if sys.platform == "win32":
        src += ".exe"

    if not os.path.exists(src):
        sys.exit(f"❌ {src} not found — run build first")

    archive = os.path.join(DIST_DIR, f"{name}-{sys.platform}")
    shutil.make_archive(archive, "zip", DIST_DIR, os.path.basename(src))
    print(f"\n✅ ZIP created: {archive}.zip")


def print_result():
    print("\n" + "=" * 60)
    print("✅ Build complete!")
    print(f"   Output → {DIST_DIR}/")
    if sys.platform == "darwin":
        print("   VirtualMouse.app  — drag to /Applications")
    elif sys.platform == "win32":
        print("   VirtualMouse.exe  — run directly, no Python needed")
    else:
        print("   VirtualMouse      — chmod +x and run")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Build Virtual Mouse installer")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    parser.add_argument("--dmg",   action="store_true", help="macOS: package to .dmg")
    parser.add_argument("--zip",   action="store_true", help="Package output to .zip")
    args = parser.parse_args()

    check_pyinstaller()

    if args.clean:
        clean()

    build()

    if args.dmg and sys.platform == "darwin":
        package_dmg()

    if args.zip:
        package_zip()

    print_result()


if __name__ == "__main__":
    main()
