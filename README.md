# Automation Scripts

A collection of various automation scripts designed to streamline common tasks, system modifications, and application management on Windows.

## Available Scripts

> [!TIP]
> **Quick Download:** You can instantly download any script by clicking the ⬇️ icon next to its name. These direct downloads are hosted natively via GitHub Releases!
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/add-sub-suffix.py) **[Add Subtitle Suffix](./add-sub-suffix/)**: A lightweight Python script to automatically detect and append standard 3-letter language suffixes (e.g., `.eng.srt`) to subtitle files.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/brave-debloater.bat) **[Brave Debloater](./brave-debloater/)**: Debloats Brave Browser by applying enterprise policies to disable telemetry, bloatware, and built-in managers.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/dbd-intro-toggler.bat) **[DBD Intro Toggler](./dbd-intro-toggler/)**: A batch script that automatically detects Steam/Epic Games installations of Dead by Daylight and toggles the startup cinematic on or off.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/display-mode-fixer.ahk) **[Display Mode Fixer](./display-mode-fixer/)**: An AutoHotkey script that forces "Second screen only" mode to prevent lag spikes while gaming when a TV is plugged in but not in use.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/hosts-blocker.ps1) **[Hosts Blocker](./hosts-blocker/)**: A PowerShell script that intelligently injects domains into the Windows `hosts` file for system-wide blocking.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/hvci-toggler.bat) **[HVCI Toggler](./hvci-toggler/)**: A batch script to easily toggle Virtualization-Based Security (VBS) and Memory Integrity (HVCI) on or off via the registry.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/idle-locker.ahk) **[Idle Locker](./idle-locker/)**: An AutoHotkey script that mutes audio and disables inputs when your monitor turns off, automatically locking your Windows session on inactivity.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/instagram-archiver.py) **[Instagram Archiver](./instagram-archiver/)**: A Python script using Instaloader to automatically backup full Instagram profiles (posts, stories, highlights) via browser cookies.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/media-converter.bat) **[Media Converter](./media-converter/)**: A batch script wrapper for FFmpeg to seamlessly and losslessly remux video files between formats (e.g. MKV to MP4).
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/mkv-cleaner.py) **[MKV Cleaner](./mkv-cleaner/)**: A Python script using `mkvmerge` to automatically batch filter MKV files, stripping out unwanted audio and subtitle tracks.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/office-installer.bat) **[Office Installer](./office-installer/)**: Provides an interactive, menu-driven installation script for Microsoft Office 365 ProPlus, allowing you to choose exactly which apps to install.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/open-hosts-file.bat) **[Open Hosts File](./open-hosts-file/)**: Automatically elevates to Administrator and opens the Windows `hosts` file in Notepad for quick editing.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/reboot-to-bios.bat) **[Reboot to BIOS](./reboot-to-bios/)**: A batch script that automatically restarts your PC and boots directly into the UEFI BIOS settings.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/spotify-uninstaller.bat) **[Spotify Uninstaller](./spotify-uninstaller/)**: Completely removes Spotify Desktop, the Spotify Microsoft Store app, Spicetify, and all residual files/registry keys.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/spotx-installer.bat) **[SpotX Installer](./spotx-installer/)**: Installs SpotX to remove ads and add features to the Spotify desktop client.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/startup-launcher.bat) **[Startup Launcher](./startup-launcher/)**: A customizable batch script designed for `shell:startup` to seamlessly launch your background scripts on boot.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/tbh-decorator.py) **[TBH Decorator](./tbh-decorator/)**: A Python script to securely modify Taskbar Hero game saves with built-in backup support.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/turn-off-monitor.bat) **[Turn Off Monitor](./turn-off-monitor/)**: Instantly puts all connected monitors to sleep via a native Windows API call.
- [⬇️](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/twitch-recorder.py) **[Twitch Recorder](./twitch-recorder/)**: Automatically monitors and records Twitch streams using `streamlink` when a specified broadcaster goes live.

## Usage

Each script is contained within its own directory and includes its own `README.md` file. Please navigate to the respective directory and read its documentation carefully before running the scripts, as some require Administrator privileges or perform deep system modifications.

## Disclaimer

> [!WARNING]
> Some of these scripts perform significant modifications to your system, including registry edits and file deletions. Always ensure you understand what a script does before running it. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. Please note that individual scripts are credited to their original authors where applicable.
