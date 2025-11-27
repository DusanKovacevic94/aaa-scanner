@echo off
echo Building aaa-scanner...
poetry run pyinstaller --noconfirm --onefile --windowed --name "aaa-scanner" scanner.py
echo Build complete. Check the 'dist' folder.
pause
