@echo off
:: Build VirtualMouse.exe on Windows
echo Installing build dependencies...
pip install pyinstaller

echo Building VirtualMouse.exe...
cd /d "%~dp0\.."
python build\build.py --clean --zip

echo.
echo Done! Find VirtualMouse.exe in dist\
pause
