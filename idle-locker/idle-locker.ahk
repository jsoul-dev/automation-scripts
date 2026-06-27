#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent()

; ===== AUTO-ELEVATE TO ADMIN =====
if (!A_IsAdmin) {
    try {
        if (A_IsCompiled)
            Run('*RunAs "' A_ScriptFullPath '"')
        else
            Run('*RunAs "' A_AhkPath '" "' A_ScriptFullPath '"')
    }
    ExitApp()
}
global Version := "1.0.0"

; ===== CONFIGURATION =====
enableMouseBlock := true       ; true = disable mouse when monitor turns off
enableKeyboardBlock := true    ; true = disable keyboard when monitor turns off
enableMute := false            ; true = mute system when monitor turns off
enableAutoOffMonitor := false  ; true = automatically turn off monitor (false = lock only)
enableAutoLockWindows := false ; true = automatically lock windows (Win+L)
enableNotifications := false   ; show tray notifications
debugMode := false             ; logs events to file at %A_ScriptDir%\MonitorLock.log
idleTimeoutMinutes := 0        ; Will be auto-detected from Windows settings (0 = auto-detect)
recheckTimeoutMinutes := 10    ; Re-check Windows timeout every X minutes
idleDetectionEnabled := true   ; Master toggle for idle detection
; ==========================

; ===== GLOBALS =====
global mouseBlocked := false
global keyboardBlocked := false
global monitorOff := false
global logFile := A_ScriptDir "\MonitorLock.log"
global startupPath := A_AppData "\Microsoft\Windows\Start Menu\Programs\Startup\MonitorLock Pro.lnk"
global idleTimeoutMs := 0  ; Will be calculated from idleTimeoutMinutes
global autoDetectTimeout := (idleTimeoutMinutes = 0)  ; Remember if we're auto-detecting
global customIdleMinutes := 10 ; For custom input fallback
global mButtonHoldStart := 0  ; Track when middle button was pressed
global mButtonHoldRequired := 2000  ; 2 seconds in milliseconds

global TimerMenu := Menu()
global currentTimerMenuName := "Idle Timer: Auto"

; ===== TRAY SETUP =====
TraySetIcon("shell32.dll", 48)  ; Padlock icon
A_TrayMenu.Delete()

A_TrayMenu.Add("Status: Ready", (*) => "")
A_TrayMenu.Disable("Status: Ready")
A_TrayMenu.Add()

A_TrayMenu.Add("Auto Mute", ToggleMute)
A_TrayMenu.Add("Off Monitor", ToggleAutoOffMonitor)
A_TrayMenu.Add("Mouse Lock", ToggleMouseLock)
A_TrayMenu.Add("Keyboard Lock", ToggleKeyboardLock)
A_TrayMenu.Add("Windows Lock", ToggleAutoLockWindows)
A_TrayMenu.Add()

A_TrayMenu.Add("Run at Startup", ToggleStartup)
A_TrayMenu.Add("Idle Detection", ToggleIdleDetection)
A_TrayMenu.Add("Notifications", ToggleNotifications)

TimerMenu.Add("Auto (Windows Settings)", SetTimerPreset.Bind(0))
TimerMenu.Add("1 min", SetTimerPreset.Bind(1))
TimerMenu.Add("2 min", SetTimerPreset.Bind(2))
TimerMenu.Add("3 min", SetTimerPreset.Bind(3))
TimerMenu.Add("5 min", SetTimerPreset.Bind(5))
TimerMenu.Add("10 min", SetTimerPreset.Bind(10))
TimerMenu.Add("15 min", SetTimerPreset.Bind(15))
TimerMenu.Add("20 min", SetTimerPreset.Bind(20))
TimerMenu.Add("30 min", SetTimerPreset.Bind(30))
TimerMenu.Add("Custom...", SetTimerCustom)

A_TrayMenu.Add(currentTimerMenuName, TimerMenu)
A_TrayMenu.Add()

A_TrayMenu.Add("Manual Lock (Ctrl+Alt+U)", (*) => LockSystem())
A_TrayMenu.Add()
A_TrayMenu.Add("Exit", (*) => CleanupAndExit())

UpdateTrayMenu()
ShowNotification("MonitorLock Pro Started", "Detecting Windows idle timeout...")

; ===== INITIALIZATION =====
; Detect Windows screen timeout setting
UpdateIdleTimeout()

; Enable toggle hotkeys from the start
Hotkey("^!u", ToggleLockHandler, "On")
Hotkey("^!t", ToggleAlwaysOnTop, "On")
; Create blocking MButton hotkeys (initially off, but with correct handlers)
Hotkey("MButton", MButtonDownHandler, "Off")
Hotkey("MButton Up", MButtonUpHandler, "Off")

; Enable pass-through hotkeys
Hotkey("~MButton", MButtonDownHandler, "On")
Hotkey("~MButton Up", MButtonUpHandler, "On")

SetTimer(CheckIdleTime, 1000)  ; Check idle time every second

; Re-check Windows timeout periodically if auto-detecting
if (autoDetectTimeout && recheckTimeoutMinutes > 0) {
    SetTimer(RecheckWindowsTimeout, recheckTimeoutMinutes * 60 * 1000)
    DebugLog("Will re-check Windows timeout every " recheckTimeoutMinutes " minutes")
}

OnExit(CleanupAndExit)

; ===== IDLE TIME DETECTION =====
UpdateIdleTimeout() {
    global idleTimeoutMinutes, idleTimeoutMs, autoDetectTimeout

    if (autoDetectTimeout) {
        newTimeout := GetWindowsScreenTimeout()

        if (newTimeout > 0 && newTimeout != idleTimeoutMinutes) {
            oldTimeout := idleTimeoutMinutes
            idleTimeoutMinutes := newTimeout
            idleTimeoutMs := idleTimeoutMinutes * 60 * 1000

            if (oldTimeout = 0) {
                DebugLog("Windows screen timeout detected: " idleTimeoutMinutes " minutes")
            } else {
                DebugLog("Windows timeout changed: " oldTimeout " -> " idleTimeoutMinutes " minutes")
                ShowNotification("Timeout Updated", "Now using " idleTimeoutMinutes " min idle timeout")
            }
        } else if (newTimeout = 0 && idleTimeoutMinutes = 0) {
            DebugLog("WARNING: Could not detect Windows timeout, defaulting to 1 minute")
            idleTimeoutMinutes := 1
            idleTimeoutMs := 60000
        }
    } else {
        DebugLog("Using manual timeout: " idleTimeoutMinutes " minutes")
        idleTimeoutMs := idleTimeoutMinutes * 60 * 1000
    }

    DebugLog("Idle timeout set to: " idleTimeoutMs "ms (" idleTimeoutMinutes " minutes)")
}

RecheckWindowsTimeout() {
    global autoDetectTimeout
    if (autoDetectTimeout) {
        DebugLog("Re-checking Windows timeout setting...")
        UpdateIdleTimeout()
    }
}

GetWindowsScreenTimeout() {
    ; Try to get AC (plugged in) screen timeout from registry
    try {
        timeoutSeconds := RegRead(
            "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\7516b95f-f776-4464-8c53-06167f40cc99\3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e",
            "ACSettingIndex")
        if (timeoutSeconds > 0) {
            minutes := Round(timeoutSeconds / 60)
            DebugLog("AC screen timeout from registry: " timeoutSeconds "s = " minutes " minutes")
            return minutes
        }
    }

    ; Alternative: Use SystemParametersInfo to get screen saver timeout
    try {
        timeout := 0
        DllCall("SystemParametersInfo", "UInt", 0x000E, "UInt", 0, "UIntP", &timeout, "UInt", 0)  ; SPI_GETSCREENSAVETIMEOUT
        if (timeout > 0) {
            minutes := Round(timeout / 60)
            DebugLog("Screen saver timeout: " timeout "s = " minutes " minutes")
            return minutes
        }
    }

    ; Try to read from current power plan
    try {
        ; Get active power scheme GUID
        activeScheme := RunWaitOne("powercfg /getactivescheme")
        if (RegExMatch(activeScheme, "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", &match)) {
            schemeGUID := match[1]
            DebugLog("Active power scheme: " schemeGUID)

            ; Get monitor timeout for this scheme (plugged in = AC)
            output := RunWaitOne("powercfg /query " schemeGUID " SUB_VIDEO VIDEOIDLE")
            if (RegExMatch(output, "Current AC Power Setting Index: 0x([0-9a-f]+)", &match)) {
                timeoutSeconds := "0x" match[1]
                timeoutSeconds := Integer(timeoutSeconds)
                if (timeoutSeconds > 0) {
                    minutes := Round(timeoutSeconds / 60)
                    DebugLog("Powercfg monitor timeout: " timeoutSeconds "s = " minutes " minutes")
                    return minutes
                }
            }
        }
    }

    DebugLog("Could not detect Windows screen timeout")
    return 0
}

RunWaitOne(command) {
    ; Use Run with hidden window and capture output to temp file
    tempFile := A_Temp "\monitorlock_" A_TickCount ".txt"

    ; Run hidden and wait for completion
    RunWait(A_ComSpec " /C " command " > `"" tempFile "`"", , "Hide")

    ; Read output
    if FileExist(tempFile) {
        output := FileRead(tempFile)
        FileDelete(tempFile)
        return output
    }
    return ""
}

CheckIdleTime() {
    global idleTimeoutMs, monitorOff, idleDetectionEnabled, enableAutoOffMonitor

    ; Skip if idle detection is disabled
    if (!idleDetectionEnabled)
        return

    ; Get system idle time in milliseconds
    idleTime := A_TimeIdle

    ; If idle time exceeds timeout and not already locked
    if (idleTime >= idleTimeoutMs && !monitorOff) {
        DebugLog("Idle timeout reached: " idleTime "ms >= " idleTimeoutMs "ms")
        if (enableAutoOffMonitor) {
            TurnOffMonitor()
        }
        MonitorTurnedOff()
    }
    ; If user became active again
    else if (idleTime < 1000 && monitorOff) {
        DebugLog("User activity detected, idle time: " idleTime "ms")
        if (enableAutoOffMonitor) {
            TurnOnMonitor()
        }
        MonitorTurnedOn()
    }
}

TurnOffMonitor() {
    ; Send command to turn off monitor
    SendMessage(0x112, 0xF170, 2, , "Program Manager")  ; SC_MONITORPOWER, 2 = off
    DebugLog("Sent monitor OFF command")
}

TurnOnMonitor() {
    ; Send command to turn on monitor
    SendMessage(0x112, 0xF170, -1, , "Program Manager")  ; SC_MONITORPOWER, -1 = on
    DebugLog("Sent monitor ON command")
}

; ===== HANDLERS =====
MonitorTurnedOff() {
    global enableMouseBlock, enableKeyboardBlock, enableMute, monitorOff, mouseBlocked, keyboardBlocked,
        enableAutoOffMonitor, enableAutoLockWindows

    if (monitorOff)
        return
    monitorOff := true

    DebugLog("Monitor turned OFF.")

    ; Switch from pass-through MButton to blocking MButton
    Hotkey("~MButton", "Off")
    Hotkey("~MButton Up", "Off")
    Hotkey("MButton", MButtonDownHandler, "On")
    Hotkey("MButton Up", MButtonUpHandler, "On")

    if (enableMouseBlock && !mouseBlocked) {
        BlockMouse(true)
        mouseBlocked := true
    }
    if (enableKeyboardBlock && !keyboardBlocked) {
        BlockKeyboard(true)
        keyboardBlocked := true
    }
    
    if (enableMute)
        SoundSetMute(true)

    if (enableAutoLockWindows) {
        if (enableMute)
            Sleep(500) ; Wait for mute to register
        DllCall("user32.dll\LockWorkStation")
        DebugLog("Windows locked via Auto Lock Windows")
    }

    if (enableAutoOffMonitor) {
        try A_TrayMenu.Rename("Status: Ready", "Status: Monitor OFF - Locked")
        ShowNotification("Monitor OFF", "Locked - Press Ctrl+Alt+U or hold MButton 2s to unlock")
    } else {
        try A_TrayMenu.Rename("Status: Ready", "Status: Locked (Monitor Auto-Off Disabled)")
        ShowNotification("Locked", "Monitor auto-off disabled - Press Ctrl+Alt+U or hold MButton 2s to unlock")
    }
}

MonitorTurnedOn() {
    global monitorOff

    if (!monitorOff)
        return

    DebugLog("Monitor turned ON - Waiting for manual unlock (Ctrl+Alt+U or MButton)")
    ShowNotification("Monitor ON", "Press Ctrl+Alt+U or hold MButton 2s to unlock")

    ; Don't change monitorOff state - keep it locked
    ; Don't unlock mouse/keyboard - wait for manual unlock
}

; ===== MIDDLE BUTTON HANDLERS =====
MButtonDownHandler(*) {
    global mButtonHoldStart, mButtonHoldRequired, mouseBlocked

    mButtonHoldStart := A_TickCount
    DebugLog("MButton pressed, starting hold timer")
    SetTimer(CheckMButtonHold, 100)
}

MButtonUpHandler(*) {
    global mButtonHoldStart

    DebugLog("MButton released")
    mButtonHoldStart := 0
    SetTimer(CheckMButtonHold, 0)  ; Stop the timer
}

CheckMButtonHold() {
    global mButtonHoldStart, mButtonHoldRequired

    if (mButtonHoldStart = 0)
        return

    holdDuration := A_TickCount - mButtonHoldStart

    if (holdDuration >= mButtonHoldRequired) {
        DebugLog("MButton held for " holdDuration "ms - toggling lock")
        SetTimer(CheckMButtonHold, 0)  ; Stop the timer
        mButtonHoldStart := 0
        ToggleLock()
    }
}

; ===== TOGGLE LOCK FUNCTION =====
ToggleLockHandler(*) {
    ToggleLock()
}

ToggleLock() {
    global mouseBlocked, keyboardBlocked, monitorOff

    ; If currently locked, unlock
    if (mouseBlocked || keyboardBlocked || monitorOff) {
        UnlockSystem()
    } else {
        ; If unlocked, lock
        LockSystem()
    }
}

LockSystem() {
    global mouseBlocked, keyboardBlocked, monitorOff, enableMute, enableMouseBlock, enableKeyboardBlock,
        enableAutoOffMonitor, enableAutoLockWindows

    ; Switch from pass-through MButton to blocking MButton
    Hotkey("~MButton", "Off")
    Hotkey("~MButton Up", "Off")
    Hotkey("MButton", MButtonDownHandler, "On")
    Hotkey("MButton Up", MButtonUpHandler, "On")

    ; Block input FIRST before turning off monitor
    if (enableMouseBlock) {
        BlockMouse(true)
        mouseBlocked := true
    }
    if (enableKeyboardBlock) {
        BlockKeyboard(true)
        keyboardBlocked := true
    }
    
    if (enableMute)
        SoundSetMute(true)
        
    if (enableAutoLockWindows) {
        if (enableMute)
            Sleep(500)
        DllCall("user32.dll\LockWorkStation")
        DebugLog("Manual Lock - Windows locked via Auto Lock Windows")
    }
    
    monitorOff := true

    try A_TrayMenu.Rename("Status: Ready", "Status: Manually Locked")
    try A_TrayMenu.Rename("Status: Disabled", "Status: Manually Locked")

    if (enableAutoOffMonitor) {
        ShowNotification("Manual Lock", "Turning off monitor...")
        DebugLog("Manual Lock triggered - waiting 3s to turn off monitor")
        ; Wait 3 seconds then force monitor off (ignore any mouse movement)
        SetTimer(ForceMonitorOff, -3000)  ; -3000 = run once after 3 seconds
    } else {
        ShowNotification("Manual Lock", "Inputs locked (monitor auto-off disabled)")
        DebugLog("Manual Lock triggered - inputs locked, monitor stays on")
    }
}

UnlockSystem() {
    global mouseBlocked, keyboardBlocked, monitorOff, mButtonHoldStart

    ; Reset middle button timer
    mButtonHoldStart := 0
    SetTimer(CheckMButtonHold, 0)

    ; Switch from blocking MButton back to pass-through MButton
    Hotkey("MButton", "Off")
    Hotkey("MButton Up", "Off")
    Hotkey("~MButton", MButtonDownHandler, "On")
    Hotkey("~MButton Up", MButtonUpHandler, "On")

    BlockMouse(false)
    mouseBlocked := false
    BlockKeyboard(false)
    keyboardBlocked := false
    SoundSetMute(false)
    monitorOff := false

    ; Try to rename from all possible locked states
    try A_TrayMenu.Rename("Status: Manually Locked", "Status: Ready")
    try A_TrayMenu.Rename("Status: Monitor OFF - Locked", "Status: Ready")
    try A_TrayMenu.Rename("Status: Locked (Monitor Auto-Off Disabled)", "Status: Ready")

    ShowNotification("Unlocked", "System restored")
    DebugLog("Manual Unlock triggered")
}

ForceMonitorOff() {
    global monitorOff
    if (monitorOff) {  ; Only if still locked
        TurnOffMonitor()
        ShowNotification("Monitor OFF", "Press Ctrl+Alt+U or hold MButton 2s to unlock")
        DebugLog("Monitor forcefully turned off after manual lock")
    }
}

; ===== BLOCKING =====
BlockMouse(block := true) {
    mouseKeys := ["LButton", "RButton", "WheelUp", "WheelDown", "WheelLeft", "WheelRight", "XButton1", "XButton2"]
    for hk in mouseKeys {
        try {
            if (block)
                Hotkey(hk, (*) => 0, "On")
            else
                Hotkey(hk, "Off")
        }
    }
    BlockInput(block ? "MouseMove" : "MouseMoveOff")
    DebugLog("Mouse " (block ? "blocked" : "unblocked") " (MButton preserved for hold-to-unlock)")
}

BlockKeyboard(block := true) {
    ; Build the keys array properly
    keys := []

    ; Add letters a-z (excluding 'l', 'd', 'p', 'f', 'm' for system/media shortcuts)
    loop 26 {
        letter := Chr(96 + A_Index)
        if (letter != "l" && letter != "d" && letter != "p" && letter != "f" && letter != "m")
            keys.Push(letter)
    }

    ; Add numbers 0-9
    loop 10
        keys.Push(String(A_Index - 1))

    ; Add function keys F1-F12
    loop 12
        keys.Push("F" A_Index)

    ; Add special keys (excluding Win, Ctrl, Alt, Delete, Enter, Up, Down, Left, Right, Space, Esc for navigation/media)
    specialKeys := ["Tab", "CapsLock", "LShift", "RShift",
        "Backspace", "Insert", "Home", "End",
        "PgUp", "PgDn"]

    for k in specialKeys
        keys.Push(k)

    if (block) {
        for k in keys {
            try {
                ; Don't block Win+L or Ctrl+Alt+Delete combinations
                if (k = "l" || k = "d")
                    continue
                Hotkey("*" k, (*) => 0, "On")
            }
        }
        DebugLog(
            "Keyboard blocked (preserving: Win+L, Ctrl+Alt+Del, Ctrl+Alt+U, Win+P, Enter, Arrows, Space, Esc, F, M for media control)"
        )
    } else {
        for k in keys {
            try {
                Hotkey("*" k, "Off")
            }
        }
        DebugLog("Keyboard unblocked")
    }
}

; ===== MENU TOGGLES =====
SetTimerPreset(mins, *) {
    global idleTimeoutMinutes, autoDetectTimeout
    idleTimeoutMinutes := mins
    autoDetectTimeout := (mins == 0)
    UpdateIdleTimeout()
    UpdateTrayMenu()
}

SetTimerCustom(*) {
    global idleTimeoutMinutes, autoDetectTimeout, customIdleMinutes
    result := InputBox("Enter idle timeout in minutes:", "Custom Idle Timer", "w200 h100", customIdleMinutes)
    if (result.Result = "OK" && IsInteger(result.Value) && result.Value > 0) {
        customIdleMinutes := result.Value
        idleTimeoutMinutes := result.Value
        autoDetectTimeout := false
        UpdateIdleTimeout()
        UpdateTrayMenu()
    }
}

ToggleIdleDetection(*) {
    global idleDetectionEnabled
    idleDetectionEnabled := !idleDetectionEnabled
    UpdateTrayMenu()
    UpdateStatusText()
    ShowNotification("Idle Detection " (idleDetectionEnabled ? "Enabled" : "Disabled"),
    idleDetectionEnabled ? "Will monitor idle time" : "Idle monitoring paused")
    DebugLog("Idle detection " (idleDetectionEnabled ? "enabled" : "disabled"))
}

ToggleMouseLock(*) {
    global enableMouseBlock
    enableMouseBlock := !enableMouseBlock
    UpdateTrayMenu()
    ShowNotification("Mouse Lock " (enableMouseBlock ? "Enabled" : "Disabled"))
}

ToggleKeyboardLock(*) {
    global enableKeyboardBlock
    enableKeyboardBlock := !enableKeyboardBlock
    UpdateTrayMenu()
    ShowNotification("Keyboard Lock " (enableKeyboardBlock ? "Enabled" : "Disabled"))
}

ToggleMute(*) {
    global enableMute
    enableMute := !enableMute
    UpdateTrayMenu()
    ShowNotification("Auto Mute " (enableMute ? "Enabled" : "Disabled"))
}

ToggleAutoLockWindows(*) {
    global enableAutoLockWindows
    enableAutoLockWindows := !enableAutoLockWindows
    UpdateTrayMenu()
    ShowNotification("Windows Lock " (enableAutoLockWindows ? "Enabled" : "Disabled"))
}

ToggleAutoOffMonitor(*) {
    global enableAutoOffMonitor
    enableAutoOffMonitor := !enableAutoOffMonitor
    UpdateTrayMenu()
    ShowNotification("Off Monitor " (enableAutoOffMonitor ? "Enabled" : "Disabled"),
    enableAutoOffMonitor ? "Monitor will turn off automatically" : "Only lock input, let Windows handle monitor")
    DebugLog("Auto-off monitor " (enableAutoOffMonitor ? "enabled" : "disabled"))
}

ToggleNotifications(*) {
    global enableNotifications
    enableNotifications := !enableNotifications
    UpdateTrayMenu()
    if (enableNotifications)
        ShowNotification("Notifications Enabled")
}

ToggleAlwaysOnTop(*) {
    try {
        activeWin := WinExist("A")
        if (activeWin) {
            WinSetAlwaysOnTop(-1, activeWin) ; -1 toggles
            exStyle := WinGetExStyle(activeWin)
            isTop := (exStyle & 0x8) ; 0x8 is WS_EX_TOPMOST
            ShowNotification("Always On Top", isTop ? "Enabled" : "Disabled")
        }
    }
}

ToggleStartup(*) {
    global startupPath
    if FileExist(startupPath) {
        try FileDelete(startupPath)
        ShowNotification("Startup Disabled")
    } else {
        ; If compiled, create shortcut to the exe
        if (A_IsCompiled) {
            try FileCreateShortcut(A_ScriptFullPath, startupPath)
        } else {
            ; If not compiled, create shortcut that runs the script with AutoHotkey
            try FileCreateShortcut(A_AhkPath, startupPath, A_ScriptDir, '"' A_ScriptFullPath '"')
        }
        ShowNotification("Startup Enabled")
    }
    UpdateTrayMenu()
}

GetStartupState() {
    global startupPath
    return FileExist(startupPath)
}

; ===== UTILITIES =====
UpdateStatusText() {
    global idleDetectionEnabled, monitorOff

    if (monitorOff) {
        return  ; Don't change status if locked
    }

    newStatus := idleDetectionEnabled ? "Status: Ready" : "Status: Disabled"

    ; Try to rename from any possible current status
    try A_TrayMenu.Rename("Status: Ready", newStatus)
    try A_TrayMenu.Rename("Status: Disabled", newStatus)
}

UpdateTrayMenu() {
    global enableMouseBlock, enableKeyboardBlock, enableMute, enableNotifications, idleDetectionEnabled
    global enableAutoOffMonitor, enableAutoLockWindows, idleTimeoutMinutes, autoDetectTimeout
    global TimerMenu, currentTimerMenuName

    if (enableAutoOffMonitor)
        A_TrayMenu.Check("Off Monitor")
    else
        A_TrayMenu.Uncheck("Off Monitor")

    if (enableMouseBlock)
        A_TrayMenu.Check("Mouse Lock")
    else
        A_TrayMenu.Uncheck("Mouse Lock")

    if (enableKeyboardBlock)
        A_TrayMenu.Check("Keyboard Lock")
    else
        A_TrayMenu.Uncheck("Keyboard Lock")

    if (enableMute)
        A_TrayMenu.Check("Auto Mute")
    else
        A_TrayMenu.Uncheck("Auto Mute")

    if (enableAutoLockWindows)
        A_TrayMenu.Check("Windows Lock")
    else
        A_TrayMenu.Uncheck("Windows Lock")

    if (idleDetectionEnabled)
        A_TrayMenu.Check("Idle Detection")
    else
        A_TrayMenu.Uncheck("Idle Detection")

    if (enableNotifications)
        A_TrayMenu.Check("Notifications")
    else
        A_TrayMenu.Uncheck("Notifications")

    if (GetStartupState())
        A_TrayMenu.Check("Run at Startup")
    else
        A_TrayMenu.Uncheck("Run at Startup")
        
    ; Update Timer Submenu checks
    TimerMenu.Uncheck("Auto (Windows Settings)")
    TimerMenu.Uncheck("1 min")
    TimerMenu.Uncheck("2 min")
    TimerMenu.Uncheck("3 min")
    TimerMenu.Uncheck("5 min")
    TimerMenu.Uncheck("10 min")
    TimerMenu.Uncheck("15 min")
    TimerMenu.Uncheck("20 min")
    TimerMenu.Uncheck("30 min")
    TimerMenu.Uncheck("Custom...")

    if (autoDetectTimeout) {
        TimerMenu.Check("Auto (Windows Settings)")
        newName := "Idle Timer: Auto"
    } else {
        checkLabel := idleTimeoutMinutes " min"
        try {
            TimerMenu.Check(checkLabel)
        } catch {
            TimerMenu.Check("Custom...")
        }
        newName := "Idle Timer: " idleTimeoutMinutes " min"
    }

    if (newName != currentTimerMenuName) {
        try A_TrayMenu.Rename(currentTimerMenuName, newName)
        currentTimerMenuName := newName
    }
}

ShowNotification(title, message := "") {
    global enableNotifications
    if (enableNotifications) {
        TrayTip(message, title)
    }
}

DebugLog(msg) {
    global debugMode, logFile
    if (debugMode) {
        try {
            FileAppend(FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") " - " msg "`n", logFile, "UTF-8")
        }
    }
}

CleanupAndExit(*) {
    global mouseBlocked, keyboardBlocked
    if (mouseBlocked) BlockMouse(false)
        if (keyboardBlocked) BlockKeyboard(false)
            SoundSetMute(false)

    ; Clean up middle button hotkeys
    try Hotkey("MButton", "Off")
    try Hotkey("MButton Up", "Off")
    SetTimer(CheckMButtonHold, 0)

    DebugLog("App exited cleanly.")
    ExitApp()
}
