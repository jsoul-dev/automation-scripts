# TBH Decorator

A Python script that interacts with the Task Bar Hero game saves, allowing for stat modification and save file backups.

## Version
Current Version: **1.3.2**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/tbh-decorator.py)

## Features
- **Stat Modification**: Interactively modifies core stats (Attack Damage, Attack Speed, Max HP, Armor) inside the save file.
- **Automatic Backups**: Automatically generates backups of your save files in the `tbh-save-backups/` directory before making any changes.
- **Save File Integrity**: Handles encryption/decryption securely to ensure the game still recognizes the save file after modification.

## Setup & Usage

1. **Install Dependencies**: This script requires a few external libraries. Run:
   ```bash
   pip install psutil cryptography
   ```
2. Run the script:
   ```bash
   python tbh-decorator.py
   ```
3. Follow the interactive console prompts to modify your save file!

## Disclaimer
This script modifies game save data. Use at your own risk and always ensure your original save files are backed up.
