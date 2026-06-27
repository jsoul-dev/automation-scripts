# SpotX Installer for Windows

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://raw.githack.com/jsoul-dev/automation-scripts/main/spotx-installer/spotx-installer.bat)

An automated installer for [SpotX](https://github.com/SpotX-Official/SpotX), providing a customized, ad-free Spotify Desktop experience.

## Overview

This batch script uses PowerShell to fetch and execute the official SpotX installation script with a predefined set of parameters. It automatically handles the uninstallation of unsupported versions and applies various visual and functional tweaks to Spotify.

## Preconfigured Parameters

The installer in this directory (`spotx-installer.bat`) is preconfigured with the following parameters to tailor your setup:

### Installation & System
- `-confirm_uninstall_ms_spoti`: Automatically uninstalls the Microsoft Store version of Spotify if found.
- `-confirm_spoti_recomended_uninstall`: Automatically uninstalls outdated/unsupported Spotify versions and installs the recommended version.
- `-block_update_on`: Blocks Spotify automatic updates to maintain the SpotX modifications.
- `-DisableStartup`: Disables Spotify autostart on Windows boot.
- `-cache_limit 500`: Limits the audio cache to 500 MB.
- `-sendversion_off`: Disables sending new versions of Spotify to SpotX developers/maintainers.
- `-start_spoti`: Automatically launches Spotify after the installation completes.
- `-no_pause`: Prevents the script from waiting for a key press before exiting.

### Visual & Experimental Features
- `-new_theme`: Activates the new theme (new right and left sidebar, cover changes).
- `-topsearchbar`: Enables the top search bar.
- `-newFullscreenMode`: Enables the new fullscreen mode.
- `-lyrics_stat spotify`: Enables the static "spotify" theme for lyrics.
- `-podcasts_on`: Retains podcasts on the homepage (does not remove them).

## Usage

1. Run the `spotx-installer.bat` file.
2. Wait for the PowerShell console to execute the remote script and apply the modifications.
3. Spotify will automatically launch once the installation is complete.

> [!WARNING]
> Do not modify the script to include parameters that contradict each other simultaneously.

## Credits & Reference

This is an original installer script based on the [SpotX-Official/SpotX](https://github.com/SpotX-Official/SpotX), simply pre-configured with the customized parameters listed above. For a full list of available parameters and advanced customization, refer to the [official parameters documentation](https://github.com/SpotX-Official/SpotX/discussions/60).
