#!/bin/bash
# Build VirtualMouse binary on Linux
set -e

cd "$(dirname "$0")/.."

echo "🔧 Installing build dependencies..."
pip install pyinstaller

# Optional: install UPX for smaller binaries
if ! command -v upx &>/dev/null; then
    echo "ℹ️  UPX not found — install for smaller binary: sudo apt install upx"
fi

echo "🏗  Building VirtualMouse..."
python build/build.py --clean --zip

echo ""
echo "✅ Done! Binary at dist/VirtualMouse"
echo "   Run with: chmod +x dist/VirtualMouse && ./dist/VirtualMouse"
