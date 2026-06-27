# Reboot to BIOS

A simple Windows batch script that instantly restarts your PC and boots directly into the BIOS (UEFI Firmware Settings) without having to aggressively mash the `Delete` or `F2` keys during startup.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Right--Click_%E2%86%92_Save_Link_As...-blue?style=for-the-badge&logo=download)](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/reboot-to-bios/reboot-to-bios.bat)

## Overview
Booting into modern UEFI firmware settings can be frustrating because Fast Boot often bypasses the keyboard initialization phase too quickly. This script utilizes the native Windows `shutdown /r /fw` command to instruct the motherboard to load directly into the UEFI BIOS on the next restart.

## Usage

1. Run `reboot-to-bios.bat`.
2. The script will automatically request Administrator privileges via UAC (User Account Control).
3. A confirmation prompt will appear in the terminal to prevent accidental restarts. Press `ENTER`.
4. Your PC will restart and boot directly into the BIOS.

> [!WARNING]
> This script relies on the `/fw` flag which is only supported on systems installed in **UEFI mode**. If your Windows installation is running in Legacy BIOS (CSM) mode, this script will return an error and will not work.
