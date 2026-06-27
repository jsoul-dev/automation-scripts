# Startup Automation Launcher

A customizable Windows batch script designed to be placed in your Windows Startup folder (`shell:startup`) to automatically launch your background automation scripts (like Python scripts or AutoHotkey scripts) silently or inside dedicated command prompts when your computer boots.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Right--Click_%E2%86%92_Save_Link_As...-blue?style=for-the-badge&logo=download)](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/startup-launcher/startup-launcher.bat)

## Setup & Usage

1. Open `startup-launcher.bat` in a text editor (like Notepad).
2. Under the `:: ======== PATHS ========` section, replace the placeholder paths (`C:\path\to\your\...`) with the actual absolute paths to your scripts.
3. Save the file.
4. Press `Win + R`, type `shell:startup`, and hit Enter. This will open your user's Startup folder.
5. Create a **shortcut** of this `startup-launcher.bat` file and place the shortcut inside the Startup folder. (Do not move the original file; just the shortcut).

Now, every time you log into Windows, this script will run and automatically launch your designated background scripts!

## Customization
The script uses `pushd` and `popd` to ensure that Python scripts run inside their respective directories (which is crucial for scripts that rely on local `config.ini` or `.json` files). You can duplicate those blocks to add as many scripts to your startup sequence as you need.
