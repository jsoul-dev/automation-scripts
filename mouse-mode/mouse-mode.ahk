#Requires AutoHotkey v2.0+
#SingleInstance Force

; ============================================================================
; Mouse Mode Switcher
; ----------------------------------------------------------------------------
; A lightweight tray utility that switches the mouse's side buttons
; (XButton1 / XButton2) between three behaviors:
;
;   Browser Mode (default) - buttons pass straight through untouched, so the
;                             mouse software's own Back/Forward mapping
;                             reaches the browser natively. Lowest latency,
;                             no synthetic key events.
;   Media Mode              - buttons become Left/Right arrow keys, handy
;                             for seeking in video/audio players.
;   Native Mode              - identical to Browser Mode at the button level
;                             (no interception at all); kept as its own
;                             clearly-labelled option for games and
;                             troubleshooting, and so Browser Mode is free to
;                             grow extra behavior later without disturbing
;                             Native Mode's "hands off, always" guarantee.
;
; Switch modes via the tray menu, by double-clicking the tray icon, or with
; the global hotkey Ctrl+Win+M. The current mode and the "Run at Startup"
; option are remembered in mouse-mode.ini next to this script/exe.
; ============================================================================


; ============================================================================
; CONSTANTS - every configurable value lives here.
; ============================================================================

APP_NAME    := "Mouse Mode Switcher"
APP_VERSION := "1.0.0"

; --- Modes ---------------------------------------------------------------
; MODE_ORDER controls both the tray menu's display order and the order
; CycleMode() steps through. MODE_LABELS supplies the human-readable text
; used in the tray menu, notifications, and the About dialog.
MODE_BROWSER := "Browser"
MODE_MEDIA   := "Media"
MODE_NATIVE  := "Native"
MODE_ORDER   := [MODE_BROWSER, MODE_MEDIA, MODE_NATIVE]
CYCLE_ORDER  := [MODE_BROWSER, MODE_MEDIA]
MODE_LABELS  := Map(
    MODE_BROWSER, "Browser Mode",
    MODE_MEDIA,   "Media Mode",
    MODE_NATIVE,  "Native Mode"
)
DEFAULT_MODE := MODE_BROWSER

; --- Hotkey (display text only -- the real binding lives in the HOTKEYS
; section below; directives can't be built from a variable) ----------------
HOTKEY_DISPLAY_TEXT := "Ctrl+Win+M"

; --- Persistent settings ---------------------------------------------------
INI_PATH := A_ScriptDir "\mouse-mode.ini"

; --- Tray icons ------------------------------------------------------------
; These numbers already include AutoHotkey's own +1 offset: AHK numbers
; icons inside a DLL starting at 1, while most published shell32 icon
; references (e.g. the numbers used in registry "DefaultIcon" strings or
; desktop.ini) start at 0 -- so AHK's number is always "reference number+1".
; If a picture ever looks wrong on your Windows build (icon sets shift a
; little between versions), right-click any shortcut -> Properties ->
; Change Icon -> browse to C:\Windows\System32\shell32.dll to preview the
; whole set and adjust below. To switch to your own .ico files later, just
; point ICON_FILE_* at them and set the matching ICON_INDEX_* to 1 --
; nothing else in the script needs to change.
; --- Compiler Directives ---------------------------------------------------
; These tell Ahk2Exe to embed the icons directly into the compiled .exe file
; so you don't need to distribute the "icons" folder alongside it.
;@Ahk2Exe-SetMainIcon icons\main.ico
;@Ahk2Exe-AddResource icons\browser.ico, 101
;@Ahk2Exe-AddResource icons\media.ico, 102
;@Ahk2Exe-AddResource icons\native.ico, 103

; --- Tray icons ------------------------------------------------------------
if A_IsCompiled {
    ICON_FILE_BROWSER  := A_ScriptFullPath
    ICON_INDEX_BROWSER := -101
    ICON_FILE_MEDIA    := A_ScriptFullPath
    ICON_INDEX_MEDIA   := -102
    ICON_FILE_NATIVE   := A_ScriptFullPath
    ICON_INDEX_NATIVE  := -103
} else {
    ICON_FILE_BROWSER  := A_ScriptDir "\icons\browser.ico"
    ICON_INDEX_BROWSER := 1
    ICON_FILE_MEDIA    := A_ScriptDir "\icons\media.ico"
    ICON_INDEX_MEDIA   := 1
    ICON_FILE_NATIVE   := A_ScriptDir "\icons\native.ico"
    ICON_INDEX_NATIVE  := 1
}

; --- Tray menu item labels (kept as constants so every Add/Check/Default
; call is guaranteed to reference the exact same text) ---------------------
STARTUP_MENU_LABEL := "Run at Startup"
NOTIFICATIONS_MENU_LABEL := "Notifications"


; ============================================================================
; RUNTIME STATE - populated for real by LoadSettings() during startup.
; ============================================================================
CurrentMode  := DEFAULT_MODE
RunAtStartup := false
NotificationsEnabled := false


; ============================================================================
; AUTO-EXECUTE
; ============================================================================
LoadSettings()
ReconcileStartupState()
SaveSettings()
BuildTray()
UpdateTray()
OnMessage(0x0404, TrayIconMessage)
Return

TrayIconMessage(wParam, lParam, msg, hwnd) {
    if (lParam = 0x0203) ; WM_LBUTTONDBLCLK
        CycleMode()
}


; ============================================================================
; HOTKEYS
; ----------------------------------------------------------------------------
; Static hotkey/#HotIf definitions are parsed when the script loads and
; can't live inside a function body, so this section is the literal
; equivalent of the spec's "RegisterHotkeys()" step.
; ============================================================================

; Global mode-cycle hotkey - works no matter which mode is currently active.
^#m::CycleMode()

; Media Mode remap ONLY. Browser Mode and Native Mode deliberately have NO
; hotkey definition for XButton1/XButton2 anywhere in this file. Confirmed
; AutoHotkey behavior: when a hotkey's #HotIf condition is false, "it
; performs its native function; that is, it passes through to the active
; window as though there is no such hotkey" -- exactly the zero-latency,
; zero-synthetic-event passthrough Browser Mode needs, with no extra code.
; (Keep this literal "Media" in sync with the MODE_MEDIA constant above.)
#HotIf CurrentMode = "Media"
XButton1::Send("{Left}")
XButton2::Send("{Right}")
#HotIf


; ============================================================================
; MODE SWITCHING
; ============================================================================

; Applies `mode`, refreshes the tray, saves settings, and (unless this is
; an internal/startup call) shows a confirmation notification.
SetMode(mode, isUserInitiated := true, *) {
    global CurrentMode

    if !MODE_LABELS.Has(mode)
        mode := DEFAULT_MODE   ; guard against a bad/unknown mode key

    CurrentMode := mode
    UpdateTray()
    SaveSettings()

    if isUserInitiated
        ShowNotification("Mouse Mode", MODE_LABELS[mode] " Enabled")
}

; Steps to the next mode in CYCLE_ORDER, wrapping back to the first.
CycleMode(*) {
    nextIndex := 1
    for index, modeKey in CYCLE_ORDER {
        if (modeKey = CurrentMode) {
            nextIndex := Mod(index, CYCLE_ORDER.Length) + 1
            break
        }
    }
    SetMode(CYCLE_ORDER[nextIndex])
}


; ============================================================================
; TRAY MENU
; ============================================================================

; Builds the static menu structure ONCE. Dynamic state (checkmarks, icon,
; tooltip) is applied separately by UpdateTray() so it can be refreshed on
; its own whenever the mode or startup setting changes.
BuildTray() {
    tray := A_TrayMenu
    tray.Delete()

    ; Non-clickable header
    tray.Add(APP_NAME, (*) => "")
    tray.Disable(APP_NAME)
    tray.Add()   ; separator

    ; Mode selection
    for modeKey in MODE_ORDER {
        if (modeKey = MODE_NATIVE)
            tray.Add()   ; separator before Native
        tray.Add(MODE_LABELS[modeKey], SetMode.Bind(modeKey, true))
    }
    tray.Add()   ; separator

    ; Options
    tray.Add(NOTIFICATIONS_MENU_LABEL, ToggleNotifications)
    tray.Add(STARTUP_MENU_LABEL, ToggleStartup)
    tray.Add()   ; separator

    ; Exit
    tray.Add("Exit", ExitApplication)
}

; Refreshes everything that depends on CurrentMode / RunAtStartup: the
; mode checkmarks, the startup checkbox, the tray icon, and the tooltip.
UpdateTray() {
    for modeKey in MODE_ORDER {
        label := MODE_LABELS[modeKey]
        if (modeKey = CurrentMode)
            A_TrayMenu.Check(label)
        else
            A_TrayMenu.Uncheck(label)
    }

    if RunAtStartup
        A_TrayMenu.Check(STARTUP_MENU_LABEL)
    else
        A_TrayMenu.Uncheck(STARTUP_MENU_LABEL)

    if NotificationsEnabled
        A_TrayMenu.Check(NOTIFICATIONS_MENU_LABEL)
    else
        A_TrayMenu.Uncheck(NOTIFICATIONS_MENU_LABEL)

    UpdateTrayIcon()
    UpdateTrayTooltip()
}

; Swaps the tray icon to match CurrentMode. Wrapped in try/catch so a bad
; icon file/index can never crash the script -- worst case, the icon just
; stays whatever it was.
UpdateTrayIcon() {
    try {
        if (CurrentMode = MODE_BROWSER)
            TraySetIcon(ICON_FILE_BROWSER, ICON_INDEX_BROWSER)
        else if (CurrentMode = MODE_MEDIA)
            TraySetIcon(ICON_FILE_MEDIA, ICON_INDEX_MEDIA)
        else if (CurrentMode = MODE_NATIVE)
            TraySetIcon(ICON_FILE_NATIVE, ICON_INDEX_NATIVE)
    } catch {
        ; Never let icon trouble take the script down.
    }
}

; Updates the text shown when hovering over the tray icon.
UpdateTrayTooltip() {
    A_IconTip := APP_NAME
        . "`n`nCurrent Mode:`n" MODE_LABELS[CurrentMode]
        . "`n`nDouble-click:`nCycle Mode"
        . "`n`n" HOTKEY_DISPLAY_TEXT "`nToggle Mode"
}


; ============================================================================
; SETTINGS PERSISTENCE (mouse-mode.ini)
; ============================================================================

; Loads Mode and RunAtStartup from the INI. Falls back to safe defaults if
; the file is missing, corrupted, or contains an unrecognized mode --
; never crashes, never leaves CurrentMode/RunAtStartup unset.
LoadSettings() {
    global CurrentMode, RunAtStartup

    try {
        if !FileExist(INI_PATH) {
            CurrentMode := DEFAULT_MODE
            RunAtStartup := false
            NotificationsEnabled := false
        } else {
            savedMode := IniRead(INI_PATH, "Settings", "Mode", DEFAULT_MODE)
            CurrentMode := MODE_LABELS.Has(savedMode) ? savedMode : DEFAULT_MODE

            savedStartup := IniRead(INI_PATH, "Settings", "RunAtStartup", "0")
            RunAtStartup := (savedStartup = "1")

            savedNotifs := IniRead(INI_PATH, "Settings", "Notifications", "0")
            NotificationsEnabled := (savedNotifs = "1")
        }
    } catch {
        CurrentMode := DEFAULT_MODE
        RunAtStartup := false
        NotificationsEnabled := false
    }
}

; Writes the current Mode and RunAtStartup to the INI. If the file can't be
; written (permissions, locked disk, etc.), fails silently rather than
; crashing -- the running script is unaffected, it just won't remember this
; particular change on the next launch.
SaveSettings() {
    try {
        IniWrite(CurrentMode, INI_PATH, "Settings", "Mode")
        IniWrite(RunAtStartup ? "1" : "0", INI_PATH, "Settings", "RunAtStartup")
        IniWrite(NotificationsEnabled ? "1" : "0", INI_PATH, "Settings", "Notifications")
    } catch {
        ; Deliberately ignored -- see comment above.
    }
}


; ============================================================================
; STARTUP SHORTCUT
; ============================================================================

; Where the Startup-folder shortcut lives (per-user Startup, no admin
; rights required).
GetStartupShortcutPath() {
    return A_Startup "\" APP_NAME ".lnk"
}

; Creates/overwrites the Startup shortcut. Handles both the plain .ahk case
; (shortcut launches the AutoHotkey interpreter with this script as its
; argument) and the compiled .exe case (shortcut points straight at it).
CreateStartupShortcut() {
    try {
        if A_IsCompiled
            FileCreateShortcut(A_ScriptFullPath, GetStartupShortcutPath(), A_ScriptDir, "", APP_NAME)
        else
            FileCreateShortcut(A_AhkPath, GetStartupShortcutPath(), A_ScriptDir, '"' A_ScriptFullPath '"', APP_NAME)
        return true
    } catch {
        return false
    }
}

RemoveStartupShortcut() {
    try {
        shortcutPath := GetStartupShortcutPath()
        if FileExist(shortcutPath)
            FileDelete(shortcutPath)
    } catch {
        ; Nothing more we can safely do from here.
    }
}

; Keeps RunAtStartup honest with what's actually on disk, so the tray
; checkbox always reflects real state rather than just the last thing
; written to the INI:
;   - If the user's last known preference was "on" but the shortcut is
;     missing, or (for a plain .ahk script) stale because AutoHotkey's own
;     path changed since the shortcut was made, silently repair it.
;   - Either way, RunAtStartup is then set to match whatever actually ends
;     up on disk. Runs once at startup, before anything else, so it never
;     produces a popup -- pure background maintenance.
ReconcileStartupState() {
    global RunAtStartup

    if RunAtStartup {
        needsRepair := !FileExist(GetStartupShortcutPath())

        if !needsRepair && !A_IsCompiled {
            try {
                FileGetShortcut(GetStartupShortcutPath(), &target, , &args)
                if (target != A_AhkPath || args != '"' A_ScriptFullPath '"')
                    needsRepair := true
            } catch {
                needsRepair := true
            }
        }

        if needsRepair
            CreateStartupShortcut()
    }

    RunAtStartup := FileExist(GetStartupShortcutPath()) ? true : false
}

; Tray menu handler for the "Run at Startup" checkbox.
ToggleStartup(*) {
    global RunAtStartup

    if RunAtStartup {
        RemoveStartupShortcut()
        RunAtStartup := false
    } else {
        if !CreateStartupShortcut() {
            ShowNotification(APP_NAME, "Couldn't create the Startup shortcut.")
            return
        }
        RunAtStartup := true
    }

    SaveSettings()
    UpdateTray()
    ShowNotification(APP_NAME, RunAtStartup ? "Run at Startup: Enabled" : "Run at Startup: Disabled")
}

; Tray menu handler for the Notifications checkbox.
ToggleNotifications(*) {
    global NotificationsEnabled
    NotificationsEnabled := !NotificationsEnabled
    SaveSettings()
    UpdateTray()
    ShowNotification(APP_NAME, "Notifications: " (NotificationsEnabled ? "Enabled" : "Disabled"))
}


; ============================================================================
; NOTIFICATIONS
; ============================================================================

; Small wrapper so every notification in the script goes through one place
; (easy to silence, retheme, or redirect later).
ShowNotification(title, text) {
    global NotificationsEnabled
    if NotificationsEnabled
        TrayTip(text, title)
}


; ============================================================================
; MENU ACTIONS
; ============================================================================

ExitApplication(*) {
    ExitApp()
}


; ============================================================================
; ADDING A FUTURE MODE (example: "Volume")
; ----------------------------------------------------------------------------
; 1. Add a constant and push it into MODE_ORDER:
;        MODE_VOLUME := "Volume"
;        MODE_ORDER  := [MODE_BROWSER, MODE_MEDIA, MODE_NATIVE, MODE_VOLUME]
; 2. Add its label:  MODE_LABELS[MODE_VOLUME] := "Volume Mode"
; 3. Add ICON_FILE_VOLUME / ICON_INDEX_VOLUME constants, plus one more
;    "else if" line in UpdateTrayIcon().
; 4. Add a new #HotIf block in the HOTKEYS section above:
;        #HotIf CurrentMode = "Volume"
;        XButton1::Send("{Volume_Down}")
;        XButton2::Send("{Volume_Up}")
;        #HotIf
; That's it -- BuildTray(), UpdateTray(), CycleMode() and SetMode() all
; already iterate MODE_ORDER/MODE_LABELS, so the new mode automatically
; appears in the tray menu and takes its place in the cycle order.
; ============================================================================
