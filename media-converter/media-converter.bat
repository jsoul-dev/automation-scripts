@echo off
setlocal enabledelayedexpansion
set "VERSION=1.0.0"
cd /d "%~dp0"

REM ═══════════════════════════════════════════════════
REM   Media Converter - Lossless FFmpeg Remuxer
REM   Converts all matching files in the current dir
REM ═══════════════════════════════════════════════════

REM --- Check ffmpeg ---
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo  FFmpeg not found. Install it by running:
    echo.
    echo    winget install ffmpeg
    echo.
    echo  Then reopen this script.
    pause
    exit /b 1
)

:menu
cls
echo.
echo   Media Converter - Lossless FFmpeg Remuxer
echo.
echo   Video
echo   -----
echo    [1]  MKV  ^<-^>  MP4
echo    [2]  MP4  ^<-^>  M4A
echo    [3]  MP4  ^<-^>  TS
echo.
echo   Photo
echo   -----
echo    [4]  PNG  ^<-^>  JPG
echo    [5]  PNG  ^<-^>  WEBP
echo    [6]  PNG  ^<-^>  ICO
echo    [7]  JPG  ^<-^>  WEBP
echo.
echo   Audio
echo   -----
echo    [8]  MP3  ^<-^>  WAV
echo    [9]  MP3  ^<-^>  M4A
echo   [10]  OGG  ^<-^>  MP3
echo.
echo    [0]  Exit
echo.
set /p "choice=  Select option: "

REM --- Video ---
if "%choice%"=="1" ( set "cat=Video" & set "fA=MKV" & set "fB=MP4" & set "sA=mkv" & set "dA=mp4" & set "xA=-c copy -map 0"          & set "hA=convert"    & set "sB=mp4" & set "dB=mkv" & set "xB=-c copy -map 0"          & set "hB=convert"     & goto pick_dir )
if "%choice%"=="2" ( set "cat=Video" & set "fA=MP4" & set "fB=M4A" & set "sA=mp4" & set "dA=m4a" & set "xA=-vn -c:a copy"           & set "hA=convert"    & set "sB=m4a" & set "dB=mp4" & set "xB=-c copy"                  & set "hB=convert"     & goto pick_dir )
if "%choice%"=="3" ( set "cat=Video" & set "fA=MP4" & set "fB=TS"  & set "sA=mp4" & set "dA=ts"  & set "xA=-c copy -f mpegts"       & set "hA=convert"    & set "sB=ts"  & set "dB=mp4" & set "xB="                        & set "hB=convert_ts"  & goto pick_dir )
REM --- Photo ---
if "%choice%"=="4" ( set "cat=Photo" & set "fA=PNG" & set "fB=JPG" & set "sA=png" & set "dA=jpg" & set "xA=-qmin 1 -q:v 1"          & set "hA=convert"    & set "sB=jpg" & set "dB=png" & set "xB="                        & set "hB=convert_img" & goto pick_dir )
if "%choice%"=="5" ( set "cat=Photo" & set "fA=PNG" & set "fB=WEBP"& set "sA=png" & set "dA=webp"& set "xA=-lossless 1"             & set "hA=convert"    & set "sB=webp"& set "dB=png" & set "xB="                        & set "hB=convert_img" & goto pick_dir )
if "%choice%"=="6" ( set "cat=Photo" & set "fA=PNG" & set "fB=ICO" & set "sA=png" & set "dA=ico" & set "xA="                        & set "hA=convert_img"& set "sB=ico" & set "dB=png" & set "xB="                        & set "hB=convert_img" & goto pick_dir )
if "%choice%"=="7" ( set "cat=Photo" & set "fA=JPG" & set "fB=WEBP"& set "sA=jpg" & set "dA=webp"& set "xA=-lossless 1"             & set "hA=convert"    & set "sB=webp"& set "dB=jpg" & set "xB=-qmin 1 -q:v 1"          & set "hB=convert"     & goto pick_dir )
REM --- Audio ---
if "%choice%"=="8" ( set "cat=Audio" & set "fA=MP3" & set "fB=WAV" & set "sA=mp3" & set "dA=wav" & set "xA="                        & set "hA=convert_img"& set "sB=wav" & set "dB=mp3" & set "xB=-c:a libmp3lame -q:a 0"  & set "hB=convert"     & goto pick_dir )
if "%choice%"=="9" ( set "cat=Audio" & set "fA=MP3" & set "fB=M4A" & set "sA=mp3" & set "dA=m4a" & set "xA=-c:a aac -b:a 320k"     & set "hA=convert"    & set "sB=m4a" & set "dB=mp3" & set "xB=-c:a libmp3lame -q:a 0"  & set "hB=convert"     & goto pick_dir )
if "%choice%"=="10" ( set "cat=Audio" & set "fA=OGG" & set "fB=MP3" & set "sA=ogg" & set "dA=mp3" & set "xA=-c:a libmp3lame -q:a 0" & set "hA=convert"    & set "sB=mp3" & set "dB=ogg" & set "xB=-c:a libvorbis -q:a 10"   & set "hB=convert"     & goto pick_dir )
if "%choice%"=="0"  ( exit /b 0 )

echo  [*] Invalid option.
timeout /t 2 >nul
goto menu

REM ═══════════════════════════════════════
REM  Direction picker for bidirectional pairs
REM ═══════════════════════════════════════
:pick_dir
cls
echo.
echo   Media Converter - Lossless FFmpeg Remuxer
echo.
echo   !cat! [!choice!] !fA! ^<-^> !fB!
echo   -----
echo.
echo    [a]  !fA! --^> !fB!
echo    [b]  !fB! --^> !fA!
echo.
echo    [0]  Back
echo.
set /p "dir=  Direction: "
set "handler="
if /i "!dir!"=="a" set "src=!sA!" & set "dst=!dA!" & set "labelS=!fA!" & set "labelD=!fB!" & set "flags=!xA!" & set "handler=!hA!"
if /i "!dir!"=="b" set "src=!sB!" & set "dst=!dB!" & set "labelS=!fB!" & set "labelD=!fA!" & set "flags=!xB!" & set "handler=!hB!"
if "!dir!"=="0" goto menu
if defined handler goto !handler!
echo  [*] Invalid direction.
timeout /t 2 >nul
goto menu

REM ═══════════════════════════════════════
REM  Standard conversion (with flags)
REM ═══════════════════════════════════════
:convert
cls
echo.
echo   Media Converter - Lossless FFmpeg Remuxer
echo.
echo   !cat! [!choice!] !labelS! --^> !labelD!
echo.
echo   Converting all .%src% to .%dst% ...
echo   -------------------------------
echo.
set "count=0"

for %%f in (*.%src%) do (
    set /a count+=1
    echo   [!count!] %%~nxf
    ffmpeg -y -i "%%f" %flags% "%%~nf.%dst%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ^> OK: %%~nf.%dst%
    ) else (
        echo        ^> FAILED
    )
)

if %count%==0 (
    echo   [*] No .%src% files found in this directory.
)

echo.
echo   Done. %count% file(s) processed.
echo.
pause
goto menu

REM ═══════════════════════════════════════
REM  TS conversion (needs -fflags +genpts before -i)
REM ═══════════════════════════════════════
:convert_ts
cls
echo.
echo   Media Converter - Lossless FFmpeg Remuxer
echo.
echo   !cat! [!choice!] TS --^> MP4
echo.
echo   Converting all .ts to .mp4 ...
echo   -------------------------------
echo.
set "count=0"

for %%f in (*.ts) do (
    set /a count+=1
    echo   [!count!] %%~nxf
    ffmpeg -y -fflags +genpts -i "%%f" -c copy -movflags +faststart "%%~nf.mp4" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ^> OK: %%~nf.mp4
    ) else (
        echo        ^> FAILED
    )
)

if %count%==0 (
    echo   [*] No .ts files found in this directory.
)

echo.
echo   Done. %count% file(s) processed.
echo.
pause
goto menu

REM ═══════════════════════════════════════
REM  Simple conversion (no flags)
REM ═══════════════════════════════════════
:convert_img
cls
echo.
echo   Media Converter - Lossless FFmpeg Remuxer
echo.
echo   !cat! [!choice!] !labelS! --^> !labelD!
echo.
echo   Converting all .%src% to .%dst% ...
echo   -------------------------------
echo.
set "count=0"

for %%f in (*.%src%) do (
    set /a count+=1
    echo   [!count!] %%~nxf
    ffmpeg -y -i "%%f" "%%~nf.%dst%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        ^> OK: %%~nf.%dst%
    ) else (
        echo        ^> FAILED
    )
)

if %count%==0 (
    echo   [*] No .%src% files found in this directory.
)

echo.
echo   Done. %count% file(s) processed.
echo.
pause
goto menu
