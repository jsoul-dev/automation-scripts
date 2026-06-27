# Open Hosts File

A simple utility script to quickly and securely edit the Windows `hosts` file.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://raw.githack.com/jsoul-dev/automation-scripts/main/open-hosts-file/open-hosts-file.bat)

## Overview
Editing the Windows `hosts` file (`C:\Windows\System32\drivers\etc\hosts`) normally requires manually opening Notepad as an Administrator before navigating to the deeply buried file. 

This script automates that entire process. When executed, it automatically requests the necessary Administrator privileges and immediately opens the `hosts` file in Notepad, ready for your edits.

## Usage

1. Run `open-hosts-file.bat`. 
2. If prompted by User Account Control (UAC), click Yes to allow Administrator access.
3. Notepad will open with the `hosts` file. Make your changes and press `Ctrl+S` to save.
