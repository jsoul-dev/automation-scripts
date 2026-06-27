@echo off
setlocal enabledelayedexpansion

set "VERSION=1.0.0"

:: HVCI + VBS + Vulnerable Driver Blocklist Toggle Script
:: Auto-elevate to Administrator
>nul 2>&1 net session
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Detect each feature robustly (handle multiple registry output formats)
set "VBS=0"
set "HVCI=0"
set "BLOCKLIST=0"

reg query "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity 2>nul | findstr /i /c:"0x1" /c:"0x00000001" /c:" 1" >nul && set "VBS=1"
reg query "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled 2>nul | findstr /i /c:"0x1" /c:"0x00000001" /c:" 1" >nul && set "HVCI=1"
reg query "HKLM\SYSTEM\CurrentControlSet\Control\CI\Config" /v VulnerableDriverBlocklistEnable 2>nul | findstr /i /c:"0x1" /c:"0x00000001" /c:" 1" >nul && set "BLOCKLIST=1"

:: Determine overall status (all three enabled -> STATUS=1)
set "STATUS=0"
if "%VBS%"=="1" if "%HVCI%"=="1" if "%BLOCKLIST%"=="1" set "STATUS=1"

:: Display current status
echo Current Status:
echo ---------------
if "%HVCI%"=="1" (
    echo   ^[+^] HVCI ^(Memory Integrity^): ENABLED
) else (
    echo   ^[-^] HVCI ^(Memory Integrity^): DISABLED
)
if "%BLOCKLIST%"=="1" (
    echo   ^[+^] Vulnerable Driver Blocklist: ENABLED
) else (
    echo   ^[-^] Vulnerable Driver Blocklist: DISABLED
)
if "%VBS%"=="1" (
    echo   ^[+^] Virtualization-Based Security: ENABLED
) else (
    echo   ^[-^] Virtualization-Based Security: DISABLED
)
echo.

:: Toggle based on status
if "%STATUS%"=="1" (
    call :print_status "INFO" "All security features are currently ENABLED."
    echo.
    choice /C YN /M "Do you want to DISABLE all three security features"
    echo.
    if errorlevel 2 (
        call :print_status "INFO" "Keeping security features enabled."
        goto :end
    ) else (
        set "FAIL=0"
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to disable VBS."
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to disable HVCI."
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Config" /v VulnerableDriverBlocklistEnable /t REG_DWORD /d 0 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to disable Blocklist."
        if "!FAIL!"=="0" (
            call :print_status "SUCCESS" "All security features have been DISABLED."
            call :print_status "WARNING" "Please REBOOT for changes to take effect."
        ) else (
            call :print_status "ERROR" "One or more operations failed."
        )
    )
) else (
    call :print_status "INFO" "One or more security features are currently DISABLED."
    echo.
    choice /C YN /M "Do you want to ENABLE all three security features"
    echo.
    if errorlevel 2 (
        call :print_status "INFO" "Keeping current configuration."
        goto :end
    ) else (
        set "FAIL=0"
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to enable VBS."
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 1 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to enable HVCI."
        reg add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Config" /v VulnerableDriverBlocklistEnable /t REG_DWORD /d 1 /f >nul 2>&1
        if errorlevel 1 set "FAIL=1" & call :print_status "ERROR" "Failed to enable Blocklist."
        if "!FAIL!"=="0" (
            call :print_status "SUCCESS" "All security features have been ENABLED."
            call :print_status "WARNING" "Please REBOOT for changes to take effect."
        ) else (
            call :print_status "ERROR" "One or more operations failed."
        )
    )
)

goto :end

:print_status
echo [%~1] %~2
goto :eof

:end
echo.
echo ============================================================
pause
endlocal
exit /b 0