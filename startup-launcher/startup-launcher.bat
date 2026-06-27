@echo off
title Startup Automation Launcher
set "VERSION=1.0.0"

:: ======== PATHS ========
set AHK_SCRIPT="C:\path\to\your\script.ahk"
set PY_DIR=C:\path\to\your\python_project
set PY_SCRIPT="script_name.py"
set INSTAGRAM_DIR=C:\path\to\your\instagram_archiver
set INSTAGRAM_SCRIPT="instagram_archiver.py"

:: ======== RUN AHK v2 SCRIPT PROPERLY ========
:: start "" "%ProgramFiles%\AutoHotkey\v2\AutoHotkey64.exe" %AHK_SCRIPT%

:: ======== RUN PYTHON SCRIPT INSIDE ITS FOLDER ========
pushd "%PY_DIR%"
start "Twitch Recorder" cmd /k python %PY_SCRIPT%
popd

:: ======== RUN INSTAGRAM ARCHIVER INSIDE ITS FOLDER ========
pushd "%INSTAGRAM_DIR%"
start "Instagram Archiver" cmd /k python %INSTAGRAM_SCRIPT%
popd

exit /b