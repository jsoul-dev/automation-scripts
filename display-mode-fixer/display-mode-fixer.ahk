; Display Monitor - Checks if display is on "Second screen only"
; Runs in system tray, auto-fixes display mode
; AutoHotkey v2.0

#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent
global Version := "1.0.0"

global Monitoring := false
global AutoFix := true  ; Auto-switch to Second screen only
global startupPath := A_Startup . "\DisplayModeMonitor.lnk"

; Setup tray icon
TraySetIcon("shell32.dll", 35)  ; Monitor icon
A_TrayMenu.Delete()  ; Remove default menu items
A_TrayMenu.Add("Start Monitoring", MenuStartMonitoring)
A_TrayMenu.Add("Stop Monitoring", MenuStopMonitoring)
A_TrayMenu.Add()  ; Separator
A_TrayMenu.Add("Auto-Fix: ON", MenuToggleAutoFix)
A_TrayMenu.Check("Auto-Fix: ON")
A_TrayMenu.Add()  ; Separator
A_TrayMenu.Add("Run at Startup", MenuToggleStartup)
if (GetStartupState()) {
    A_TrayMenu.Check("Run at Startup")
}
A_TrayMenu.Add()  ; Separator
A_TrayMenu.Add("Check Now", MenuCheckNow)
A_TrayMenu.Add()  ; Separator
A_TrayMenu.Add("Exit", MenuExit)

; Disable Stop Monitoring initially
A_TrayMenu.Disable("Stop Monitoring")

; Auto-start monitoring
StartMonitoring()

MenuStartMonitoring(*) {
    StartMonitoring()
}

MenuStopMonitoring(*) {
    StopMonitoring()
}

MenuToggleAutoFix(*) {
    global AutoFix
    AutoFix := !AutoFix
    if (AutoFix) {
        A_TrayMenu.Check("Auto-Fix: ON")
        A_TrayMenu.Rename("Auto-Fix: ON", "Auto-Fix: ON")
    } else {
        A_TrayMenu.Uncheck("Auto-Fix: ON")
        A_TrayMenu.Rename("Auto-Fix: ON", "Auto-Fix: OFF")
    }
}

MenuToggleStartup(*) {
    global startupPath
    if FileExist(startupPath) {
        try FileDelete(startupPath)
        A_TrayMenu.Uncheck("Run at Startup")
    } else {
        ; If compiled, create shortcut to the exe
        if (A_IsCompiled) {
            try FileCreateShortcut(A_ScriptFullPath, startupPath)
        } else {
            ; If not compiled, create shortcut that runs the script with AutoHotkey
            try FileCreateShortcut(A_AhkPath, startupPath, A_ScriptDir, '"' A_ScriptFullPath '"')
        }
        A_TrayMenu.Check("Run at Startup")
    }
}

GetStartupState() {
    global startupPath
    return FileExist(startupPath)
}

MenuCheckNow(*) {
    CheckDisplay()
}

MenuExit(*) {
    ExitApp()
}

StartMonitoring() {
    global Monitoring
    Monitoring := true
    A_TrayMenu.Disable("Start Monitoring")
    A_TrayMenu.Enable("Stop Monitoring")
    SetTimer(CheckDisplay, 60000)  ; Check every 60 seconds
    CheckDisplay()  ; Check immediately
}

StopMonitoring() {
    global Monitoring
    Monitoring := false
    A_TrayMenu.Enable("Start Monitoring")
    A_TrayMenu.Disable("Stop Monitoring")
    SetTimer(CheckDisplay, 0)
}

CheckDisplay(*) {
    ; Skip check if a fullscreen game is running (like League)
    if (IsFullscreenAppRunning()) {
        return
    }
    
    ; Get display configuration using Windows API
    QDC_ONLY_ACTIVE_PATHS := 0x00000002
    numPathElements := 0
    numModeElements := 0
    
    ; DllCall to get buffer sizes
    result := DllCall("User32.dll\GetDisplayConfigBufferSizes",
        "UInt", QDC_ONLY_ACTIVE_PATHS,
        "UInt*", &numPathElements,
        "UInt*", &numModeElements,
        "Int")
    
    ; Get monitor count via AHK
    MonCount := MonitorGetCount()
    
    ; Check virtual screen size
    virtualWidth := SysGet(78)  ; SM_CXVIRTUALSCREEN
    primaryWidth := SysGet(16)  ; SM_CXSCREEN
    isExtended := (virtualWidth > primaryWidth)
    
    ; Determine mode based on number of paths
    if (numPathElements = 2 && !isExtended) {
        topology := "Duplicate"
    } else if (numPathElements = 2 && isExtended) {
        topology := "Extend"
    } else if (numPathElements = 1 && MonCount = 1) {
        ; Only check total displays if needed (avoids PowerShell call when possible)
        if (result = 0) {  ; API call succeeded
            topology := "SecondOnly"
        } else {
            ; Fallback: Check if multiple displays exist
            totalDisplays := GetTotalDisplays()
            
            if (totalDisplays >= 2) {
                topology := "SecondOnly"
            } else {
                topology := "PCOnly"
            }
        }
    } else if (MonCount >= 2 && !isExtended) {
        topology := "Duplicate"
    } else if (MonCount >= 2 && isExtended) {
        topology := "Extend"
    } else {
        topology := "Unknown"
    }
    
    ; Take action if NOT on "Second screen only"
    if (topology != "SecondOnly" && topology != "") {
        if (AutoFix) {
            ; Auto-fix: Switch to Second screen only (silently)
            SwitchToSecondScreenOnly()
        } else {
            ; Just warn
            ShowWarning(topology)
        }
    } else if (topology = "SecondOnly") {
        ; Already on correct mode, do nothing
        return
    }
}

IsFullscreenAppRunning() {
    ; Check if a fullscreen application or specific game is running
    
    ; List of game processes to skip checking (only in-game, not clients)
    gameProcesses := ["League of Legends.exe"]
    
    ; Check if any game process is running
    for process in gameProcesses {
        if (ProcessExist(process)) {
            return true
        }
    }
    
    ; Also check if a fullscreen window is active
    try {
        hwnd := WinGetID("A")
        
        ; Get window style
        style := WinGetStyle(hwnd)
        exStyle := WinGetExStyle(hwnd)
        
        ; Check if it's a fullscreen window (no borders, no title bar)
        ; WS_CAPTION = 0xC00000, WS_THICKFRAME = 0x40000
        hasCaption := (style & 0xC00000)
        hasThickFrame := (style & 0x40000)
        
        ; If window has no caption and no thick frame, it's likely fullscreen
        if (!hasCaption && !hasThickFrame) {
            ; Additional check: window covers entire screen
            WinGetPos(&x, &y, &w, &h, hwnd)
            screenWidth := SysGet(16)
            screenHeight := SysGet(17)
            
            if (w >= screenWidth && h >= screenHeight) {
                return true
            }
        }
    }
    
    return false
}

SwitchToSecondScreenOnly() {
    ; Use DisplaySwitch.exe to switch to external only (Second screen only)
    ; /external = Second screen only
    Run("DisplaySwitch.exe /external", , "Hide")
}

GetTotalDisplays() {
    ; Use WMI to check total connected displays (hidden PowerShell)
    try {
        script := 'Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBasicDisplayParams | Measure-Object | Select-Object -ExpandProperty Count'
        result := RunWait('powershell.exe -WindowStyle Hidden -NoProfile -Command "' . script . '"', , "Hide")
        return result
    } catch {
        return 0
    }
}

ShowWarning(currentMode) {
    ; Create warning popup
    WarningGui := Gui("+AlwaysOnTop +ToolWindow", "Display Warning")
    WarningGui.BackColor := "FFEEEE"
    WarningGui.SetFont("s14 bold cRed")
    WarningGui.Add("Text", "x10 y10 w330 Center", "⚠️ WARNING ⚠️")
    WarningGui.SetFont("s11 norm cBlack")
    WarningGui.Add("Text", "x10 y50 w330 Center", "Display is NOT on`n`"Second screen only`" mode!")
    WarningGui.SetFont("s9 cGray")
    WarningGui.Add("Text", "x10 y100 w330 Center", "Detected mode: " . currentMode)
    WarningGui.SetFont("s10 norm")
    
    ; Add Fix button
    FixBtn := WarningGui.Add("Button", "x75 y135 w90 h30", "Fix Now")
    FixBtn.OnEvent("Click", (*) => (SwitchToSecondScreenOnly(), WarningGui.Destroy()))
    
    OKBtn := WarningGui.Add("Button", "x185 y135 w90 h30", "Ignore")
    OKBtn.OnEvent("Click", (*) => WarningGui.Destroy())
    
    WarningGui.OnEvent("Close", (*) => WarningGui.Destroy())
    WarningGui.Show("w350 h185")
    
    ; Play warning sound
    SoundBeep(750, 300)
    
    ; Auto-close after 15 seconds
    SetTimer(() => (WarningGui ? WarningGui.Destroy() : 0), 15000)
}