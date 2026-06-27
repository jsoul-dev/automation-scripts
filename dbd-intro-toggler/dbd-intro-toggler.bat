@echo off
setlocal enabledelayedexpansion

set "VERSION=1.0.0"

:: Dead by Daylight Intro Toggle Script (Steam + Epic Games, One-Go Disable/Enable)

:: Ensure admin rights
>nul 2>&1 net session
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "GAME_NAME=Dead by Daylight"
set "MOVIE_PATH=DeadByDaylight\Content\Movies\AdditionalLoadingScreen"
set "VIDEO_FILENAME=LoadingScreenPostLogin.bk2"

echo =============================================================
echo   !GAME_NAME! Intro Video Toggle Script (Steam + Epic)
echo =============================================================
echo.

:: ----- Locate Steam -----
set "STEAM_PATH="
if exist "%ProgramFiles(x86)%\Steam\steam.exe" set "STEAM_PATH=%ProgramFiles(x86)%\Steam"
if not defined STEAM_PATH if exist "%ProgramFiles%\Steam\steam.exe" set "STEAM_PATH=%ProgramFiles%\Steam"

set "STEAM_GAME="
if defined STEAM_PATH (
    call :find_steam_game "%STEAM_PATH%"
)

:: ----- Locate Epic Games Store installation -----
set "EPIC_GAME="
call :find_epic_game

:: ----- If neither found, quit -----
if not defined STEAM_GAME if not defined EPIC_GAME (
    call :print_status "ERROR" "No Dead by Daylight installation found."
    goto :end
)

:: ----- Choice: Disable or Enable -----
echo [1] Disable Intro (Steam + Epic)
echo [2] Enable Intro  (Steam + Epic)
echo.
choice /C 12 /M "Choose an option"
set "CHOICE=%errorlevel%"

echo.

if "%CHOICE%"=="1" (
    if defined STEAM_GAME call :disable_intro "%STEAM_GAME%\%MOVIE_PATH%" "%VIDEO_FILENAME%" "Steam"
    if defined EPIC_GAME call :disable_intro "%EPIC_GAME%\%MOVIE_PATH%" "%VIDEO_FILENAME%" "Epic"
) else if "%CHOICE%"=="2" (
    if defined STEAM_GAME call :enable_intro "%STEAM_GAME%\%MOVIE_PATH%" "%VIDEO_FILENAME%" "Steam"
    if defined EPIC_GAME call :enable_intro "%EPIC_GAME%\%MOVIE_PATH%" "%VIDEO_FILENAME%" "Epic"
)

goto :end

:: ===== FUNCTIONS =====

:find_steam_game
set "STEAM_DIR=%~1"
set "VDF_FILE=%STEAM_DIR%\steamapps\libraryfolders.vdf"

:: Main library
if exist "%STEAM_DIR%\steamapps\common\%GAME_NAME%" (
    set "STEAM_GAME=%STEAM_DIR%\steamapps\common\%GAME_NAME%"
)

:: Extra libraries
if not defined STEAM_GAME if exist "%VDF_FILE%" (
    for /f "usebackq tokens=* delims=" %%L in ("%VDF_FILE%") do (
        echo %%L | findstr /R /C:"\"path\"" >nul
        if !errorlevel! equ 0 (
            for /f "tokens=2 delims=:" %%P in ("%%L") do (
                set "LIBPATH=%%P"
                set "LIBPATH=!LIBPATH:"=!"
                set "LIBPATH=!LIBPATH: =!"
                set "LIBPATH=!LIBPATH:/=\!"
                if exist "!LIBPATH!\steamapps\common\%GAME_NAME%" (
                    set "STEAM_GAME=!LIBPATH!\steamapps\common\%GAME_NAME%"
                )
            )
        )
    )
)
goto :eof

:find_epic_game
:: Epic Games Store manifest locations (common paths)
set "EGS_MANIFESTS[0]=%ProgramData%\Epic\EpicGamesLauncher\Data\Manifests"
set "EGS_MANIFESTS[1]=%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows"
set "EGS_MANIFESTS[2]=%ProgramFiles(x86)%\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher\Saved\Config\Windows"

:: Check each manifest location
for /L %%i in (0,1,2) do (
    if defined EGS_MANIFESTS[%%i] (
        set "MANIFEST_DIR=!EGS_MANIFESTS[%%i]!"
        if exist "!MANIFEST_DIR!" (
            call :search_epic_manifests "!MANIFEST_DIR!"
            if defined EPIC_GAME goto :eof
        )
    )
)

:: Fallback: Check default Epic Games installation
if not defined EPIC_GAME (
    set "DEFAULT_EPIC=C:\Program Files\Epic Games\DeadByDaylight"
    if exist "!DEFAULT_EPIC!" (
        set "EPIC_GAME=!DEFAULT_EPIC!"
    )
)
goto :eof

:search_epic_manifests
set "MANIFEST_DIR=%~1"

:: Look for .item files (manifest files) in the directory
for %%F in ("%MANIFEST_DIR%\*.item") do (
    call :parse_epic_manifest "%%F"
    if defined EPIC_GAME goto :eof
)
goto :eof

:parse_epic_manifest
set "MANIFEST_FILE=%~1"

:: Read the manifest file and look for Dead by Daylight
for /f "usebackq tokens=* delims=" %%L in ("%MANIFEST_FILE%") do (
    set "LINE=%%L"
    
    :: Check if this manifest is for Dead by Daylight
    echo !LINE! | findstr /I /C:"Dead by Daylight" >nul 2>&1
    if !errorlevel! equ 0 set "IS_DBD=true"
    
    :: Look for installation path if this is DBD
    if defined IS_DBD (
        echo !LINE! | findstr /R /C:"\"InstallLocation\"" >nul 2>&1
        if !errorlevel! equ 0 (
            :: Extract the path from the JSON-like format
            for /f "tokens=2 delims=:" %%P in ("!LINE!") do (
                set "INSTALL_PATH=%%P"
                :: Clean up the path (remove quotes, commas, spaces)
                set "INSTALL_PATH=!INSTALL_PATH:"=!"
                set "INSTALL_PATH=!INSTALL_PATH:,=!"
                set "INSTALL_PATH=!INSTALL_PATH: =!"
                
                :: Verify the path exists and contains DBD
                if exist "!INSTALL_PATH!\DeadByDaylight" (
                    set "EPIC_GAME=!INSTALL_PATH!\DeadByDaylight"
                    goto :eof
                ) else if exist "!INSTALL_PATH!" (
                    set "EPIC_GAME=!INSTALL_PATH!"
                    goto :eof
                )
            )
        )
    )
)
goto :eof

:disable_intro
set "VIDEO_DIR=%~1"
set "VIDEO_FILE=%VIDEO_DIR%\%~2"
set "BACKUP_FILE=%VIDEO_FILE%.bak"
set "PLATFORM=%~3"

if not exist "%VIDEO_DIR%" (
    call :print_status "ERROR" "%PLATFORM% video directory not found: %VIDEO_DIR%"
    goto :eof
)

if exist "%VIDEO_FILE%" (
    :: If .bak already exists, delete it first
    if exist "%BACKUP_FILE%" (
        del /F /Q "%BACKUP_FILE%"
    )
    
    ren "%VIDEO_FILE%" "%~2.bak"
    if !errorlevel! equ 0 (
        call :print_status "SUCCESS" "Intro video disabled on %PLATFORM%."
    ) else (
        call :print_status "ERROR" "Failed to disable intro on %PLATFORM%."
    )
) else if exist "%BACKUP_FILE%" (
    call :print_status "INFO" "Intro video already DISABLED on %PLATFORM%."
) else (
    call :print_status "WARNING" "Intro video not found at %PLATFORM%."
)
goto :eof

:enable_intro
set "VIDEO_DIR=%~1"
set "VIDEO_FILE=%VIDEO_DIR%\%~2"
set "BACKUP_FILE=%VIDEO_FILE%.bak"
set "PLATFORM=%~3"

if not exist "%VIDEO_DIR%" (
    call :print_status "ERROR" "%PLATFORM% video directory not found: %VIDEO_DIR%"
    goto :eof
)

if exist "%BACKUP_FILE%" (
    ren "%BACKUP_FILE%" "%~2"
    if !errorlevel! equ 0 (
        call :print_status "SUCCESS" "Intro video restored on %PLATFORM%."
    ) else (
        call :print_status "ERROR" "Failed to restore intro on %PLATFORM%."
    )
) else if exist "%VIDEO_FILE%" (
    call :print_status "INFO" "Intro video already ENABLED on %PLATFORM%."
) else (
    call :print_status "WARNING" "Intro video not found at %PLATFORM%."
)
goto :eof

:print_status
echo [%~1] %~2
goto :eof

:end
echo.
echo =============================================================
echo.
pause
endlocal