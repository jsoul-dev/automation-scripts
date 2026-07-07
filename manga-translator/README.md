# Manga Translator
An automated Python script that batch-translates raw manga pages from Japanese to English using the MangaTranslate API. 

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://github.com/jsoul-dev/automation-scripts/releases/latest/download/manga-translator.py)

## Overview
This script scans a directory for image files, uploads them to the online translator service, and downloads the cleaned, translated results into a `tr/` subfolder. It automatically manages API session credits and user IDs to ensure continuous bulk processing.

## Features
- **Batch Processing**: Automatically loops through all images in a specified folder.
- **Session Management**: Automatically rotates temporary user sessions to bypass API credit limits.
- **Resumption**: Skips over images that have already been translated and saved in the output directory.

## Usage
Simply run the python script:
```bash
python manga-translator.py
```
You can edit the `folder`, `src_lang`, and `out_lang` variables at the top of the script to customize its behavior.
