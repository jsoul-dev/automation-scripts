# Hosts Blocker

A robust PowerShell script that intelligently injects domain-blocking entries into the Windows `hosts` file to block telemetry, ads, or specific websites.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/hosts-blocker.ps1)

## Features
- **Smart Grouping**: Instead of blindly appending entries to the end of your `hosts` file, it intelligently groups related entries together.
- **Duplicate Prevention**: Skips entries that have already been added to prevent bloat.
- **Auto-Elevation**: Automatically requests Administrator privileges to modify the protected system file.

## Usage
1. Open the `hosts.txt` file located in this directory.
2. Add any domains you wish to block (one per line).
3. Right-click `hosts-blocker.ps1` and select **Run with PowerShell**.
4. The script will automatically elevate its privileges, read the text file, and intelligently inject your custom entries into your `C:\Windows\System32\drivers\etc\hosts` file without duplicating existing ones.
