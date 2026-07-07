# WiFi Password Viewer
A lightweight, terminal-based batch script that extracts and views saved Wi-Fi network passwords on Windows. 

## Version
Current Version: **2.0**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/wifi-pass-viewer.bat)

## Overview
This script queries the native Windows WLAN API via `netsh` to enumerate all cached user profiles (previously connected Wi-Fi networks). It then provides an interactive console interface to select a network and extract the plaintext password (key content) stored on the system.

## Features
- **Profile Discovery**: Automatically finds all saved Wi-Fi networks.
- **Interactive Menu**: Type the ID of the network you wish to view.
- **Plaintext Extraction**: Retrieves the cleartext password using Windows native commands without requiring third-party tools.
