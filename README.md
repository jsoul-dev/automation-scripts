# Automation Scripts

A collection of various automation scripts designed to streamline common tasks, system modifications, and application management on Windows.

## Available Scripts

- **[Add Subtitle Suffix](./add-sub-suffix/)**: A lightweight Python script to automatically detect and append standard 3-letter language suffixes (e.g., `.eng.srt`) to subtitle files. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/add-sub-suffix/add-sub-suffix.py)
- **[Brave Debloater](./brave-debloater/)**: Debloats Brave Browser by applying enterprise policies to disable telemetry, bloatware, and built-in managers. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/brave-debloater/brave-debloater.bat)
- **[DBD Intro Toggler](./dbd-intro-toggler/)**: A batch script that automatically detects Steam/Epic Games installations of Dead by Daylight and toggles the startup cinematic on or off. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/dbd-intro-toggler/dbd-intro-toggler.bat)
- **[Display Mode Fixer](./display-mode-fixer/)**: An AutoHotkey script that forces "Second screen only" mode to prevent lag spikes while gaming when a TV is plugged in but not in use. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/display-mode-fixer/display-mode-fixer.ahk)
- **[Hosts Blocker](./hosts-blocker/)**: A PowerShell script that intelligently injects domains into the Windows `hosts` file for system-wide blocking. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/hosts-blocker/hosts-blocker.ps1)
- **[HVCI Toggler](./hvci-toggler/)**: A batch script to easily toggle Virtualization-Based Security (VBS) and Memory Integrity (HVCI) on or off via the registry. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/hvci-toggler/hvci-toggler.bat)
- **[Idle Locker](./idle-locker/)**: An AutoHotkey script that mutes audio and disables inputs when your monitor turns off, automatically locking your Windows session on inactivity. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/idle-locker/idle-locker.ahk)
- **[Instagram Archiver](./instagram-archiver/)**: A Python script using Instaloader to automatically backup full Instagram profiles (posts, stories, highlights) via browser cookies. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/instagram-archiver/instagram-archiver.py)
- **[Media Converter](./media-converter/)**: A batch script wrapper for FFmpeg to seamlessly and losslessly remux video files between formats (e.g. MKV to MP4). - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/media-converter/media-converter.bat)
- **[MKV Cleaner](./mkv-cleaner/)**: A Python script using `mkvmerge` to automatically batch filter MKV files, stripping out unwanted audio and subtitle tracks. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/mkv-cleaner/mkv-cleaner.py)
- **[Office Installer](./office-installer/)**: Provides an interactive, menu-driven installation script for Microsoft Office 365 ProPlus, allowing you to choose exactly which apps to install. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/office-installer/office-installer.bat)
- **[Open Hosts File](./open-hosts-file/)**: Automatically elevates to Administrator and opens the Windows `hosts` file in Notepad for quick editing. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/open-hosts-file/open-hosts-file.bat)
- **[Reboot to BIOS](./reboot-to-bios/)**: A batch script that automatically restarts your PC and boots directly into the UEFI BIOS settings. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/reboot-to-bios/reboot-to-bios.bat)
- **[Spotify Uninstaller](./spotify-uninstaller/)**: Completely removes Spotify Desktop, the Spotify Microsoft Store app, Spicetify, and all residual files/registry keys. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/spotify-uninstaller/spotify-uninstaller.bat)
- **[SpotX Installer](./spotx-installer/)**: Installs SpotX to remove ads and add features to the Spotify desktop client. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/spotx-installer/spotx-installer.bat)
- **[Startup Launcher](./startup-launcher/)**: A customizable batch script designed for `shell:startup` to seamlessly launch your background scripts on boot. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/startup-launcher/startup-launcher.bat)
- **[Turn Off Monitor](./turn-off-monitor/)**: Instantly puts all connected monitors to sleep via a native Windows API call. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/turn-off-monitor/turn-off-monitor.bat)
- **[Twitch Recorder](./twitch-recorder/)**: Automatically monitors and records Twitch streams using `streamlink` when a specified broadcaster goes live. - [?? Right-Click -> Save Link As...](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/twitch-recorder/twitch-recorder.py)

## Usage

Each script is contained within its own directory and includes its own `README.md` file. Please navigate to the respective directory and read its documentation carefully before running the scripts, as some require Administrator privileges or perform deep system modifications.

## Disclaimer

> [!WARNING]
> Some of these scripts perform significant modifications to your system, including registry edits and file deletions. Always ensure you understand what a script does before running it. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. Please note that individual scripts are credited to their original authors where applicable.
