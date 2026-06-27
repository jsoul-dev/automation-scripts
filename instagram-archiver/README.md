# Instagram Archiver

An automated Python script that leverages `instaloader` to download and archive complete Instagram profiles, including posts, stories, and highlights.

## Version
Current Version: **1.0.0**

> [!NOTE]
> This script is currently pending an update/rewrite. Some features or login mechanisms may be outdated or unoptimized. It is also currently a monolithic, single-file script (spaghetti code) that needs to be modularized and split into multiple files for better organization and maintainability.

## Features
- **Comprehensive Archiving**: Downloads all available media from target profiles.
- **Cookie Authentication**: Bypasses login roadblocks and 401 errors by using your active browser session cookies.
- **Auto-Config Generation**: Automatically generates a boilerplate `config.json` file on its first run for easy setup.
- **Multiple Targets**: Can archive multiple profiles sequentially based on your config.

## Dependencies

Before running the script, you must install the required Python packages:

```bash
pip install instaloader colorama
```

## Setup & Usage

1. **Run once to generate config**:
   Open a terminal in this directory and run the script:
   ```bash
   python instagram-archiver.py
   ```
   The script will exit and generate a `config.json` file in the same directory.

2. **Configure your session and targets**:
   Open the newly created `config.json`. You will need to provide your Instagram cookies and the list of profiles you want to archive.

### How to get your Instaloader Browser Cookies:

To prevent rate-limiting and login errors, you need to provide your browser's session cookies:

1. Log in to Instagram through your web browser.
2. Open your browser's **DevTools** (F12 or Right-Click -> Inspect).
3. Navigate to the **Application** tab (or "Storage" in Firefox).
4. Under the "Storage" section on the left sidebar, expand **Cookies** and click on `https://www.instagram.com`.
5. Look for the following keys and copy their values into your `config.json`:
   - `csrftoken`
   - `sessionid`
   - `ds_user_id`
   - `mid`
   - `ig_did`

6. **Run the script again**:
   Once your `config.json` is populated with your cookies and target profiles, run the script again:
   ```bash
   python instagram-archiver.py
   ```

## Usage Warning
> [!CAUTION]
> Using this script acts as an automated bot on your account. Running it multiple times a day or trying to download massive amounts of data too quickly may result in your Instagram account being temporarily restricted or banned. For safety, it is highly recommended to run this script **no more than once a day**.

## Security Note
> [!WARNING]
> Your `config.json` and `session-*` files contain your personal Instagram authentication tokens. **Do not share these files.** They are already included in the `.gitignore` to prevent accidental uploads.

## Credits
This script utilizes the excellent [Instaloader](https://instaloader.github.io/) library.
