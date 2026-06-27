@echo off

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "VERSION=1.0.0"
set "REG_PATH=HKLM\SOFTWARE\Policies\BraveSoftware\Brave"

echo Applying Brave policies (Version: %VERSION%)...
echo.

reg delete "%REG_PATH%" /ve /f >nul 2>&1

reg add "%REG_PATH%" /v BackgroundModeEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v BraveRewardsDisabled /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v BraveWalletDisabled /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v BraveVPNDisabled /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v BraveNewsDisabled /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v BraveTalkDisabled /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v BraveStatsPingEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v UrlKeyedAnonymizedDataCollectionEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v SafeBrowsingExtendedReportingEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v FeedbackSurveysEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v BraveWebDiscoveryEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v BraveP3AEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v PasswordManagerEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v AutofillAddressEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v AutofillCreditCardEnabled /t REG_DWORD /d 0 /f
reg add "%REG_PATH%" /v PromptForDownloadLocation /t REG_DWORD /d 1 /f
reg add "%REG_PATH%" /v MetricsReportingEnabled /t REG_DWORD /d 0 /f

echo.
echo Done! Brave debloated successfully.
echo Restart Brave or reload brave://policy.
echo.
pause
