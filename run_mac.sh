#!/bin/sh
# EeveeMon on macOS -- run from source.
# Requirements: Python 3.8+ with tkinter (python.org installer
# or Homebrew `brew install python-tk`), and Pillow.
set -e
cd "$(dirname "$0")"
python3 -m pip install --quiet Pillow
python3 fetch_sprites.py
exec python3 eeveemon.py
