@echo off
setlocal enabledelayedexpansion

set "VERSION=2.0.0"

color 0a
title WIFI CREDENTIAL EXTRACTOR v%VERSION%
cls

echo.
echo  WIFI CREDENTIAL EXTRACTOR v%VERSION%
echo  ------------------------------
echo.
echo [*] Querying Windows WLAN API for cached profiles...
ping 127.0.0.1 -n 2 >nul

set count=0
for /f "tokens=2 delims=:" %%a in ('netsh wlan show profiles ^| findstr "All User Profile"') do (
    set /a count+=1
    set "val=%%a"
    set "profile[!count!]=!val:~1!"
)

if %count%==0 (
    echo [x] No networks found in range.
    echo.
    pause
    color 07
    exit /b
)

echo.
echo [+] Found %count% vulnerable network(s):
echo ----------------------------------------
for /l %%i in (1, 1, %count%) do (
    ping 127.0.0.1 -n 1 >nul
    echo    [%%i] !profile[%%i]!
)
echo ----------------------------------------

:MENU
echo.
set "choice="
set /p choice="root@system:~# Select target ID (or 'q' to abort): "

if /i "%choice%"=="q" (
    echo.
    echo [*] Aborting operation. Clearing logs... Connection closed.
    ping 127.0.0.1 -n 2 >nul
    color 07
    exit /b
)

set "target="
for /l %%i in (1, 1, %count%) do (
    if "%%i"=="%choice%" set "target=!profile[%%i]!"
)

if not defined target (
    echo [x] Invalid target ID.
    goto MENU
)

echo.
echo [*] Targeting network: !target!
ping 127.0.0.1 -n 1 >nul
echo [*] Initiating handshake sequence...
ping 127.0.0.1 -n 2 >nul

<nul set /p="[*] Extracting hash payload: "
for /l %%i in (1, 1, 10) do (
    <nul set /p="*"
    ping 127.0.0.1 -n 1 -w 100 >nul
)
echo SUCCESS
ping 127.0.0.1 -n 1 >nul

set "password="
for /f "tokens=2 delims=:" %%p in ('netsh wlan show profile name^="!target!" key^=clear ^| findstr "Key Content"') do (
    set "val=%%p"
    set "password=!val:~1!"
)

if defined password (
    echo.
    echo [+] CREDENTIALS OBTAINED:
    echo ----------------------------------------
    echo  TARGET SSID  : !target!
    echo  PLAINTEXT KEY: !password!
    echo ----------------------------------------
) else (
    echo.
    echo [-] Decryption failed for '!target!'. Network may be OPEN or secured differently.
)

goto MENU
