@echo off
rem EeveeMon one-click restart
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'eeveemon' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
cd /d C:\Users\xinglechun\eeveemon
start "" "D:\Program Files (x86)\python.exe" eeveemon.py
