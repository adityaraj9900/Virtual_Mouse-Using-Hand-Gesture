#!/bin/bash
# Build VirtualMouse.app + optional .dmg on macOS
set -e

cd "$(dirname "$0")/.."

echo "🔧 Installing build dependencies..."
pip install pyinstaller

echo "🏗  Building VirtualMouse.app..."
python build/build.py --clean

if command -v create-dmg &>/dev/null; then
    echo "📦 Packaging .dmg..."
    python build/build.py --dmg
    echo "✅ dist/VirtualMouse.dmg ready"
else
    echo "ℹ️  create-dmg not found — install with: brew install create-dmg"
    echo "   Falling back to hdiutil..."
    python build/build.py --dmg
fi

echo ""
echo "✅ Done! Drag dist/VirtualMouse.app to /Applications"
