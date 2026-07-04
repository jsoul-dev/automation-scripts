@echo off

:: =====================================================
::  Office 365 ProPlus Installer
::  Version 1.2.0
:: =====================================================

:: Self-elevate to administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: ---- Configuration ----

set "VERSION=1.2.0"

:: Console dimensions
title Office 365 ProPlus Installer
mode con: cols=53 lines=38
color 07

:: ---- Default App States (1=EXCLUDE, 0=INCLUDE) ----

set "app_Access=1"
set "app_Excel=0"
set "app_Groove=1"
set "app_Lync=1"
set "app_M365Companion=1"
set "app_OneDrive=1"
set "app_OneNote=1"
set "app_Outlook=1"
set "app_OutlookForWindows=1"
set "app_PowerPoint=0"
set "app_Publisher=1"
set "app_Teams=1"
set "app_Bing=1"
set "app_Word=0"
set "opt_Shortcuts=0"

:: =====================================================
::  Main Menu
:: =====================================================

:MENU
cls
echo =====================================================
echo           Office 365 ProPlus Installer
echo                 (Version: %VERSION%)
echo =====================================================
echo.
echo  Current Configuration (toggle options by number):
echo.
echo  --- CORE APPS ---
call :ShowOption 1  Word           %app_Word%
call :ShowOption 2  Excel          %app_Excel%
call :ShowOption 3  PowerPoint     %app_PowerPoint%
call :ShowOption 4  Outlook        %app_Outlook%
call :ShowOption 5  OneNote        %app_OneNote%
call :ShowOption 6  Access         %app_Access%
call :ShowOption 7  Publisher      %app_Publisher%
echo.
echo  --- COMMUNICATION ---
call :ShowOption 8  Teams          %app_Teams%
call :ShowOption 9  Skype/Lync     %app_Lync%
call :ShowOption 10 "New Outlook"  %app_OutlookForWindows%
echo.
echo  --- EXTRAS ---
call :ShowOption 11 OneDrive       %app_OneDrive%
call :ShowOption 12 Groove         %app_Groove%
call :ShowOption 13 "M365 Companion" %app_M365Companion%
call :ShowOption 14 "Bing Search"  %app_Bing%
echo.
echo  --- OPTIONS ---
call :ShowOption 15 "Desktop Shortcuts" %opt_Shortcuts%
echo.
echo =====================================================
echo   [A] Include ALL Apps     [D] Default Selection
powershell -Command "Write-Host '  [I] Start Installation' -ForegroundColor Cyan -NoNewline; Write-Host '   [E] Export Config'"
echo   [K] Skip to Activation   [Q] Quit
echo =====================================================
echo.
set /p "choice=Enter option: "

if /i "%choice%"=="1" if "%app_Word%"=="0" (set "app_Word=1") else (set "app_Word=0")
if /i "%choice%"=="2" if "%app_Excel%"=="0" (set "app_Excel=1") else (set "app_Excel=0")
if /i "%choice%"=="3" if "%app_PowerPoint%"=="0" (set "app_PowerPoint=1") else (set "app_PowerPoint=0")
if /i "%choice%"=="4" if "%app_Outlook%"=="0" (set "app_Outlook=1") else (set "app_Outlook=0")
if /i "%choice%"=="5" if "%app_OneNote%"=="0" (set "app_OneNote=1") else (set "app_OneNote=0")
if /i "%choice%"=="6" if "%app_Access%"=="0" (set "app_Access=1") else (set "app_Access=0")
if /i "%choice%"=="7" if "%app_Publisher%"=="0" (set "app_Publisher=1") else (set "app_Publisher=0")
if /i "%choice%"=="8" if "%app_Teams%"=="0" (set "app_Teams=1") else (set "app_Teams=0")
if /i "%choice%"=="9" if "%app_Lync%"=="0" (set "app_Lync=1") else (set "app_Lync=0")
if /i "%choice%"=="10" if "%app_OutlookForWindows%"=="0" (set "app_OutlookForWindows=1") else (set "app_OutlookForWindows=0")
if /i "%choice%"=="11" if "%app_OneDrive%"=="0" (set "app_OneDrive=1") else (set "app_OneDrive=0")
if /i "%choice%"=="12" if "%app_Groove%"=="0" (set "app_Groove=1") else (set "app_Groove=0")
if /i "%choice%"=="13" if "%app_M365Companion%"=="0" (set "app_M365Companion=1") else (set "app_M365Companion=0")
if /i "%choice%"=="14" if "%app_Bing%"=="0" (set "app_Bing=1") else (set "app_Bing=0")
if /i "%choice%"=="15" if "%opt_Shortcuts%"=="0" (set "opt_Shortcuts=1") else (set "opt_Shortcuts=0")

if /i "%choice%"=="A" (
    set "app_Access=0"
    set "app_Excel=0"
    set "app_Groove=0"
    set "app_Lync=0"
    set "app_M365Companion=0"
    set "app_OneDrive=0"
    set "app_OneNote=0"
    set "app_Outlook=0"
    set "app_OutlookForWindows=0"
    set "app_PowerPoint=0"
    set "app_Publisher=0"
    set "app_Teams=0"
    set "app_Bing=0"
    set "app_Word=0"
    set "opt_Shortcuts=0"
)

if /i "%choice%"=="D" (
    set "app_Access=1"
    set "app_Excel=0"
    set "app_Groove=1"
    set "app_Lync=1"
    set "app_M365Companion=1"
    set "app_OneDrive=1"
    set "app_OneNote=1"
    set "app_Outlook=1"
    set "app_OutlookForWindows=1"
    set "app_PowerPoint=0"
    set "app_Publisher=1"
    set "app_Teams=1"
    set "app_Bing=1"
    set "app_Word=0"
    set "opt_Shortcuts=0"
)

if /i "%choice%"=="Q" exit /b
if /i "%choice%"=="I" goto CONFIRM
if /i "%choice%"=="K" goto ACTIVATE_ONLY
if /i "%choice%"=="E" goto EXPORT_CONFIG
goto MENU

:: =====================================================
::  Confirm & Install
:: =====================================================

:CONFIRM
cls
echo =====================================================
echo              Confirm Installation
echo =====================================================
echo.
powershell -Command "Write-Host ' WARNING: If you have any existing Office' -ForegroundColor Yellow; Write-Host ' installation, it will be AUTOMATICALLY' -ForegroundColor Yellow; Write-Host ' UNINSTALLED and replaced with this one.' -ForegroundColor Yellow"
echo.
powershell -Command "Write-Host ' NOTE: To ADD apps (e.g. Teams) to an existing' -ForegroundColor Cyan; Write-Host ' Office installation (e.g. Word, Excel, PPT),' -ForegroundColor Cyan; Write-Host ' you MUST include ALL apps you want to keep.' -ForegroundColor Cyan; Write-Host ' Apps not selected will be UNINSTALLED by ODT.' -ForegroundColor Cyan"
echo.
echo  Apps to be INSTALLED:
if "%app_Word%"=="0" echo    - Word
if "%app_Excel%"=="0" echo    - Excel
if "%app_PowerPoint%"=="0" echo    - PowerPoint
if "%app_Outlook%"=="0" echo    - Outlook
if "%app_OneNote%"=="0" echo    - OneNote
if "%app_Access%"=="0" echo    - Access
if "%app_Publisher%"=="0" echo    - Publisher
if "%app_Teams%"=="0" echo    - Teams
if "%app_Lync%"=="0" echo    - Skype/Lync
if "%app_OutlookForWindows%"=="0" echo    - New Outlook
if "%app_OneDrive%"=="0" echo    - OneDrive
if "%app_Groove%"=="0" echo    - Groove
if "%app_M365Companion%"=="0" echo    - M365 Companion
if "%app_Bing%"=="0" echo    - Bing Search
echo.
echo =====================================================
echo.
set /p "confirm=Proceed with installation? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

echo.
echo [1/4] Creating C:\Office directory...
if not exist "C:\Office" mkdir "C:\Office"

echo [2/4] Creating Configuration.xml...
call :WriteXml "C:\Office\Configuration.xml"

echo [3/4] Downloading Office Deployment Tool (setup.exe)...
powershell -Command "Invoke-WebRequest -Uri 'https://officecdn.microsoft.com/pr/wsus/setup.exe' -OutFile 'C:\Office\setup.exe'"

if not exist "C:\Office\setup.exe" (
    echo.
    echo ERROR: Failed to download setup.exe
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo [4/4] Running Office installation...
echo.
"C:\Office\setup.exe" /configure "C:\Office\Configuration.xml"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Office installation exited with code %errorlevel%
    echo Check the logs above for details.
    echo.
    pause
)

echo.
echo Cleaning up installation files...
rmdir /s /q "C:\Office" 2>nul

echo.
echo =====================================================
echo          Installation Complete!
echo =====================================================
echo.

if "%opt_Shortcuts%"=="0" call :CreateShortcuts

set /p "activate=Do you want to activate Office? (Y/N): "
if /i "%activate%"=="Y" call :Activate

echo.
echo Done! Press any key to exit...
pause >nul
exit /b

:: =====================================================
::  Activate Only (Skip Installation)
:: =====================================================

:ACTIVATE_ONLY
cls
echo =====================================================
echo          Office Activation Only
echo =====================================================
echo.
echo This option is for users who already have Office
echo installed and just want to activate it.
echo.

call :Activate

echo.
echo Done! Press any key to exit...
pause >nul
exit /b

:: =====================================================
::  Export Configuration
:: =====================================================

:EXPORT_CONFIG
cls
echo =====================================================
echo           Export Configuration File
echo =====================================================
echo.
echo Generating Configuration.xml based on your selection...
echo.

:: Get Downloads folder path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "{374DE290-123F-4565-9164-39C4925E467B}" 2^>nul') do set "downloads=%%b"
if not defined downloads set "downloads=%USERPROFILE%\Downloads"

call :WriteXml "%downloads%\Configuration.xml"

powershell -Command "Write-Host 'Configuration.xml saved to:' -ForegroundColor Green"
echo   %downloads%\Configuration.xml
echo.
echo =====================================================
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:: =====================================================
::  Subroutines
:: =====================================================

:: ---- :ShowOption  num  name  state ----
:: Displays a single menu option with color-coded status.

:ShowOption
setlocal EnableDelayedExpansion
set "num=%~1"
set "name=%~2"
set "state=%~3"

:: Pad number for alignment
if %num% LSS 10 (set "numpad= [%num%]") else (set "numpad=[%num%]")

:: Pad name to 18 chars
set "name=%name%                  "
set "name=!name:~0,18!"

if "%state%"=="0" (
    powershell -Command "Write-Host '  %numpad% !name! [INCLUDE]' -ForegroundColor Green"
) else (
    echo   %numpad% !name! [EXCLUDE]
)
endlocal
goto :eof

:: ---- :WriteXml  "output_path" ----
:: Generates the ODT Configuration.xml file at the given path.

:WriteXml
set "xmlpath=%~1"
(
echo ^<Configuration^>
echo   ^<Add OfficeClientEdition="64" Channel="Current"^>
echo     ^<Product ID="O365ProPlusRetail"^>
echo       ^<Language ID="en-us" /^>
if "%app_Access%"=="1" echo       ^<ExcludeApp ID="Access" /^>
if "%app_Excel%"=="1" echo       ^<ExcludeApp ID="Excel" /^>
if "%app_Groove%"=="1" echo       ^<ExcludeApp ID="Groove" /^>
if "%app_Lync%"=="1" echo       ^<ExcludeApp ID="Lync" /^>
if "%app_M365Companion%"=="1" echo       ^<ExcludeApp ID="M365Companion" /^>
if "%app_OneDrive%"=="1" echo       ^<ExcludeApp ID="OneDrive" /^>
if "%app_OneNote%"=="1" echo       ^<ExcludeApp ID="OneNote" /^>
if "%app_Outlook%"=="1" echo       ^<ExcludeApp ID="Outlook" /^>
if "%app_OutlookForWindows%"=="1" echo       ^<ExcludeApp ID="OutlookForWindows" /^>
if "%app_PowerPoint%"=="1" echo       ^<ExcludeApp ID="PowerPoint" /^>
if "%app_Publisher%"=="1" echo       ^<ExcludeApp ID="Publisher" /^>
if "%app_Teams%"=="1" echo       ^<ExcludeApp ID="Teams" /^>
if "%app_Bing%"=="1" echo       ^<ExcludeApp ID="Bing" /^>
if "%app_Word%"=="1" echo       ^<ExcludeApp ID="Word" /^>
echo     ^</Product^>
echo   ^</Add^>
echo   ^<Display Level="Full" AcceptEULA="True" /^>
echo   ^<Updates Enabled="true" /^>
echo ^</Configuration^>
) > "%xmlpath%"
goto :eof

:: ---- :Activate ----
:: Launches Microsoft Activation Scripts (MAS) for Office activation.

:Activate
echo =====================================================
echo        Office Activation Instructions
echo =====================================================
echo.
echo When the activation menu appears:
echo   Select Option [2] Ohook - for permanent Office activation
echo.
echo =====================================================
echo.
echo Launching Microsoft Activation Scripts...
echo.
powershell -Command "try { irm https://get.activated.win | iex } catch { Write-Host 'Primary method blocked, using DNS-over-HTTPS fallback...' -ForegroundColor Yellow; iex (curl.exe -s --doh-url https://1.1.1.1/dns-query https://get.activated.win ^| Out-String) }"
goto :eof

:: ---- :CreateShortcuts ----
:: Copies Start Menu shortcuts for included apps to the Desktop.

:CreateShortcuts
echo =====================================================
echo         Creating Desktop Shortcuts...
echo =====================================================
echo.
set "startmenu=C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
set "desktop=%USERPROFILE%\Desktop"

if "%app_Word%"=="0" copy /y "%startmenu%\Word.lnk" "%desktop%\" >nul 2>&1
if "%app_Excel%"=="0" copy /y "%startmenu%\Excel.lnk" "%desktop%\" >nul 2>&1
if "%app_PowerPoint%"=="0" copy /y "%startmenu%\PowerPoint.lnk" "%desktop%\" >nul 2>&1
if "%app_Outlook%"=="0" copy /y "%startmenu%\Outlook.lnk" "%desktop%\" >nul 2>&1
if "%app_OneNote%"=="0" copy /y "%startmenu%\OneNote.lnk" "%desktop%\" >nul 2>&1
if "%app_Access%"=="0" copy /y "%startmenu%\Access.lnk" "%desktop%\" >nul 2>&1
if "%app_Publisher%"=="0" copy /y "%startmenu%\Publisher.lnk" "%desktop%\" >nul 2>&1
if "%app_Teams%"=="0" copy /y "%startmenu%\Microsoft Teams.lnk" "%desktop%\" >nul 2>&1
if "%app_Lync%"=="0" copy /y "%startmenu%\Skype for Business.lnk" "%desktop%\" >nul 2>&1
if "%app_OutlookForWindows%"=="0" copy /y "%startmenu%\Outlook (new).lnk" "%desktop%\" >nul 2>&1
if "%app_OneDrive%"=="0" copy /y "%startmenu%\OneDrive.lnk" "%desktop%\" >nul 2>&1
if "%app_Groove%"=="0" copy /y "%startmenu%\OneDrive for Business.lnk" "%desktop%\" >nul 2>&1

powershell -Command "Write-Host 'Desktop shortcuts created.' -ForegroundColor Green"
echo.
goto :eof

