@echo off

REM open-hosts-file.bat  - self-elevate then open hosts in Notepad

set "VERSION=1.0.0"

:: If not elevated, relaunch this script elevated
>nul 2>&1 net session
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set "HOSTS=%windir%\System32\drivers\etc\hosts"

if not exist "%HOSTS%" (
    echo Hosts file not found at "%HOSTS%".
    pause
    exit /b 1
)

echo Opening hosts file in Notepad (running elevated)...
start "" notepad "%HOSTS%"
exit /b 0
