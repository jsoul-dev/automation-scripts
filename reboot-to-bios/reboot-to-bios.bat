@echo off

set "VERSION=1.0.0"

:: ================================================================
:: Automatically restarts the PC into BIOS (UEFI Firmware Settings)
:: Self-elevates to Administrator and asks for confirmation.
:: ================================================================

:: Set window title
title Reboot to BIOS (UEFI Firmware Settings)

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Confirmation prompt
echo ===========================================
echo   REBOOT TO BIOS (UEFI Firmware Settings)
echo ===========================================
echo.
echo This will restart your computer immediately
echo and boot into your BIOS / UEFI firmware settings.
echo.
set /p confirm="Press ENTER to continue or close this window to cancel... "
echo.

:: Final confirmation before restart
echo Restarting now...
timeout /t 2 >nul

:: Perform reboot into BIOS
shutdown /r /fw /t 1
