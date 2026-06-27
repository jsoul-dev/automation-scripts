# MKV Cleaner

An automated Python script designed to batch process MKV files and strip out unwanted audio and subtitle tracks, such as director's commentary and foreign languages, using `mkvmerge`.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Right--Click_%E2%86%92_Save_Link_As...-blue?style=for-the-badge&logo=download)](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/mkv-cleaner/mkv-cleaner.py)

> [!NOTE]
> This script is currently pending an update/rewrite. It is a monolithic, single-file script (spaghetti code) that needs to be modularized and split into multiple files for better organization and maintainability.

## Dependencies

Before running the script, you must install the required dependencies:

1. **Python Packages**:
   ```bash
   pip install colorama tqdm
   ```
2. **MKVToolNix**: You must have [MKVToolNix](https://mkvtoolnix.download/) installed and ensure that `mkvmerge` is added to your system's PATH.

## Setup & Usage

1. Open `mkv-cleaner.py` in a text editor.
2. Edit the variables inside the `---------- CONFIG (edit here) ----------` block at the top of the file to set your preferred default audio and subtitle languages (e.g., `KEEP_AUDIO_LANG = "eng"`).
3. Place your `.mkv` files in the same directory as the script (or run the script within the directory containing your files).
4. Run the script:
   ```bash
   python mkv-cleaner.py
   ```
5. The cleaned, remuxed files will be saved in the `Filtered` subfolder by default.

## Credits

This script is an original wrapper built around the incredibly powerful [MKVToolNix](https://mkvtoolnix.download/) toolset, specifically utilizing `mkvmerge` to process the files losslessly.
