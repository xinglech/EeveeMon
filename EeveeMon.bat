@echo off
rem EeveeMon launcher -- no hardcoded paths:
rem   1) prefer the bundled exe (zero dependencies), then
rem   2) any python found on PATH, then
rem   3) the py launcher (py -3).
rem Works on any machine regardless of where Python lives.
cd /d "%~dp0"

if exist "dist\EeveeMon.exe" (
    start "" "dist\EeveeMon.exe"
    exit /b 0
)

set "PY="
for /f "delims=" %%p in ('where python 2^>nul') do (
    if not defined PY set "PY=%%p"
)
if defined PY (
    start "" "%PY%" eeveemon.py
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    start "" py -3 eeveemon.py
    exit /b 0
)

echo EeveeMon could not find Python on this machine.
echo Either double-click dist\EeveeMon.exe, or install Python
echo from https://www.python.org/downloads/ and try again.
pause
