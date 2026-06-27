# Add Subtitle Suffix

A lightweight Python utility that scans directories for `.srt` subtitle files and automatically appends the correct 3-letter language suffix (e.g., `.eng.srt`) based on the filename.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Right--Click_%E2%86%92_Save_Link_As...-blue?style=for-the-badge&logo=download)](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/add-sub-suffix/add-sub-suffix.py)

## Features
- **Smart Detection**: Reads the filename to detect language keywords (e.g., "english", "spanish (latin american)") and maps them to the standard ISO 639-2 format.
- **Idempotency**: Safely ignores files that already have a proper 3-letter suffix so it can be run multiple times safely.
- **Recursive Directory Processing**: Designed to be placed in a root directory; it scans through subdirectories to rename the contents natively.

## Setup & Usage

1. **No external dependencies required**. The script runs entirely on Python's built-in standard library (`os`, `re`).
2. Drop the `add-sub-suffix.py` script into your base directory containing folders of subtitles.
3. Run the script:
   ```bash
   python add-sub-suffix.py
   ```
4. It will output to the console which files were successfully renamed, which were ignored, and which could not be mapped to a language.

## Customization
If you need to support additional languages, open the script in a text editor and add them to the `LANGUAGE_SUFFIXES` dictionary map at the top.
