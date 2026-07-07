# Manga Translator
An automated Python script that batch-translates raw manga pages from Japanese to English using the MangaTranslate API. 

## Version
Current Version: **2.0.1**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/manga-translator.py)

## Requirements
This script requires the `requests` and `colorama` libraries to make HTTP calls to the translation API and provide formatted console output.
You can install them via pip:
```bash
pip install requests colorama
```

## Usage
1. Make sure you have python installed along with the `requests` library.
2. Place `manga-translator.py` anywhere on your computer and double-click it (or run `python manga-translator.py`). 
3. It will automatically generate an `input` and `output` folder next to the script.
4. Drop your raw manga folders inside the `input` directory (e.g. `input/uzumaki/image1.png`).
5. Run the script again. It will automatically scan all folders in the `input` directory, upload the images for translation, and save the English versions in the `output` directory under `[Folder Name] [MTL]`.
6. If an output folder already exists for a manga, the script will skip it and proceed to the next folder.

## Rate Limits
The API typically restricts usage to **10 images per IP address**. When the script hits this limit, it will display a `Too many requests` warning and automatically pause for 60 seconds. 
If you connect to a new VPN server during this pause, the script will instantly resume translation right where it left off!

## Features
- **Batch Processing**: Automatically loops through all images in a specified folder.
- **Session Management**: Automatically rotates temporary user sessions to bypass API credit limits.
- **Resumption**: Skips over folders that have already been translated and saved in the output directory.
