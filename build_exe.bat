@echo off
rem EeveeMon one-file exe build: fetch sprites (if missing) + pyinstaller
python fetch_sprites.py || exit /b 1
python -m pip install --quiet pyinstaller
python -m PyInstaller --onefile --windowed --name EeveeMon --add-data "sprites;sprites" --clean --noconfirm eeveemon.py
echo.
echo Built: dist\EeveeMon.exe
