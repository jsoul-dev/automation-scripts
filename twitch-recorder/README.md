# Twitch Recorder

An automated Python script that monitors a specific Twitch channel and automatically records the stream using `streamlink` and `ffmpeg` whenever the streamer goes live.

## Version
Current Version: **1.0.0**

[![Download Script](https://img.shields.io/badge/Download-Script-blue?style=for-the-badge&logo=download)](https://raw.githubusercontent.com/jsoul-dev/automation-scripts/main/twitch-recorder/twitch-recorder.py)

> [!NOTE]
> This script is currently pending an update/rewrite. It currently suffers from a bug where it stops recording if the video exceeds 4 hours in length or 9GB in size, causing subsequent footage of long streams to be lost. Additionally, it is a monolithic, single-file script (spaghetti code) that needs to be modularized and split into multiple files for better organization. For future updates, it may be best to avoid passing custom `streamlink` args and just rely on its default behavior.

## Dependencies

Before running the script, you must install the required Python packages and system dependencies:

1. **Python Packages**:
   ```bash
   pip install requests streamlink colorama
   ```
2. **FFmpeg**: You must have `ffmpeg` installed and added to your system's PATH.

## Setup & Usage

1. **Run once to generate config**:
   Open a terminal in this directory and run the script:
   ```bash
   python twitch_auto_live_recorder_v6_stable.py
   ```
   The script will exit and generate a `config.ini` file in the same directory.

2. **Configure your API keys and target**:
   Open the newly created `config.ini`. You will need to provide your Twitch API credentials (`client_id` and `client_secret`), as well as the target `streamer` username.
   - You can get Twitch API credentials by registering an application on the [Twitch Developer Console](https://dev.twitch.tv/console).

3. **Run the script again**:
   Once your `config.ini` is populated, run the script again. It will continuously monitor the channel and start recording when the streamer goes live.

## Security Note
> [!WARNING]
> Your `config.ini` file contains your Twitch API credentials. **Do not share this file.** It is already included in the `.gitignore` to prevent accidental uploads.

## Credits
This script utilizes the following powerful tools under the hood:
- **[Streamlink](https://streamlink.github.io/)**: A CLI utility used to extract and pipe the live video streams.
- **[FFmpeg](https://ffmpeg.org/)**: Used for processing and remuxing the downloaded streams into MP4 format.
