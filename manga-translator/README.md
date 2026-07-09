# Manga Translator
An automated Python script that batch-translates raw manga pages from Japanese to English using the MangaTranslate API. 

## Version
Current Version: **2.0.9**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/manga-translator.py)

## Requirements
This script requires the `requests` and `colorama` libraries to make HTTP calls to the translation API and provide formatted console output.
You can install them via pip:
```bash
pip install requests colorama
```

## Directory Structure
For the script to work properly, your files should be organized like this:
```text
manga-translator/
├── manga-translator.py
├── proxies/                        <-- (Optional) Drop proxy lists here (.txt or .csv)
│   └── proxies.txt
├── input/                          <-- Place your raw manga folders here
│   ├── Chapter 1/
│   │   ├── 01.png
│   │   └── 02.png
│   └── Chapter 2/
│       ├── 01.png
│       └── 02.png
└── output/                         <-- Translated manga will appear here
    ├── Chapter 1 [MTL]/
    │   ├── 01.png
    │   └── 02.png
    └── Chapter 2 [MTL]/
```

## Usage
1. Install Python and the required libraries (`requests`, `colorama`).
2. Run `manga-translator.py`. On its first run, it will automatically create the `input` and `output` folders for you.
3. Drop your raw manga folders inside the `input` directory (as shown in the structure above).
4. Run the script again. It will scan all folders **and `.zip`/`.cbz` archives**, upload the images, and save the translated versions in the `output` directory.

### Smart Archive Support (ZIP/CBZ)
You can directly drop `.zip` and `.cbz` manga archives into the `input` directory! The script will safely extract them to a temporary workspace, translate the images while preserving any internal nested folders, and seamlessly package them back into a `.cbz` archive in the `output` directory!
5. **Smart Resumption (Save Credits!)**: If the script is interrupted or aborts due to rate limits, it will **NOT** re-translate the entire folder from scratch! When you restart it, it will automatically detect which images already exist in the `output` folder, skip them to save your credits and time, and instantly resume on the exact image it left off on!

## Proxies & Rate Limits
The API typically restricts usage to **10 images per IP address**. 
- **Automated Proxy Rotation**: To bypass this limit entirely, create a `proxies` folder next to the script and drop in your proxy lists (Standard IP:PORT or Geonode CSVs). The script will automatically load them and instantly rotate to a new IP whenever the rate limit is hit, allowing you to translate massive batches of manga hands-free!
- **Manual VPN Rotation**: If you don't use proxies, the script will display a `Too many requests` warning and prompt you. You can either wait 60 seconds (and change your VPN IP manually during the countdown to resume instantly), or abort the current run.

## Features
- **Archive Support**: Native extraction and repackaging for `.zip` and `.cbz` manga archives, fully preserving internal nested folder structures!
- **Configurable Models**: Supports various translation models (CTD, CTD2, HTD, etc.) and fonts by changing the variables at the top of the script.
- **Smart Resumption**: Skips over individual images that have already been translated and saved in the output directory.
- **Proxy Auto-Rotation**: Automatically juggles thousands of proxies to bypass API limits on the fly.
