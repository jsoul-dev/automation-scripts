#!/usr/bin/env python3
"""
Instagram Profile Archiver using Instaloader
Downloads complete Instagram profiles with highest quality settings
Uses session cookies to avoid 401 errors
"""

import instaloader
import sys
import os
import time
import json
from pathlib import Path
import io
import contextlib
from colorama import init, Fore, Back, Style

VERSION = "1.0.2"

# Initialize colorama
init(autoreset=True)

def print_header(text, width=70):
    """Print a colored header in a box"""
    padding = (width - len(text) - 2) // 2
    print(f"\n{Fore.CYAN}{Style.BRIGHT}+{'-' * (width - 2)}+")
    print(f"|{' ' * padding}{text}{' ' * (width - len(text) - padding - 2)}|")
    print(f"+{'-' * (width - 2)}+{Style.RESET_ALL}")

def print_subheader(text, width=70):
    """Print a colored subheader"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{text}")
    print(f"{Fore.YELLOW}{'-' * len(text)}{Style.RESET_ALL}")

def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message"""
    print(f"{Fore.CYAN}[INFO] {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}[WARN] {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")

def print_progress(text):
    """Print progress message"""
    print(f"{Fore.MAGENTA}[->] {text}{Style.RESET_ALL}")

def print_stat(label, value, width=None):
    """Print a stat line"""
    if width is None:
        width = 15
    print(f"{Fore.WHITE}{label.ljust(width)} : {Fore.CYAN}{Style.BRIGHT}{value}{Style.RESET_ALL}")

def archive_profile(target_username, session_data=None, output_dir=None, profile_name=None):
    """
    Archive an Instagram profile with all media types
    
    Args:
        target_username: Instagram username to download
        session_data: Dictionary with Instagram session cookies
        output_dir: Directory to save downloads (default: current directory)
        profile_name: Friendly name for the profile folder
    """
    
    # Initialize counters
    stats = {
        'profile_pic': False,
        'posts_new': 0,
        'posts_skipped': 0,
        'stories_new': 0,
        'stories_skipped': 0,
        'highlights_new': 0,
        'highlights_skipped': 0
    }
    
    # Create Instaloader instance with rate limit friendly settings
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern='',
        max_connection_attempts=5,
        request_timeout=300,
        resume_prefix='resume_state',
        fatal_status_codes=[],
        sleep=True,
        quiet=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    )
    
    # Create organized folder structure
    if output_dir and profile_name:
        profile_folder = Path(output_dir) / profile_name
        profile_folder.mkdir(parents=True, exist_ok=True)
        
        posts_folder = profile_folder / "posts"
        highlights_folder = profile_folder / "highlights"
        stories_folder = profile_folder / "stories"
        
        posts_folder.mkdir(exist_ok=True)
        highlights_folder.mkdir(exist_ok=True)
        stories_folder.mkdir(exist_ok=True)
        
        os.chdir(output_dir)
    elif output_dir:
        os.chdir(output_dir)
        profile_folder = Path(output_dir)
    else:
        profile_folder = Path.cwd()
    
    # Load session if provided
    if session_data:
        print_header("AUTHENTICATION")
        print()
        try:
            username = session_data['username']
            cookies = session_data['cookies']
            
            print_progress(f"Loading session for {username}...")
            print_info("Using browser cookies...")
            
            L.context._session.cookies.update(cookies)
            
            sessionid = L.context._session.cookies.get('sessionid')
            if sessionid and sessionid != "":
                print_success(f"Session ID loaded: {sessionid[:20]}...")
            else:
                print_warning("Session ID is empty!")
            
            L.context.username = username
            
            print_progress("Testing authentication...")
            f = io.StringIO()
            with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
                try:
                    test_result = L.test_login()
                except Exception as e:
                    test_result = None
                    captured = f.getvalue()
                    print_error(f"Login test raised: {str(e)[:100]}")
            
            if test_result:
                print_success(f"Authentication successful: @{test_result}")
                
                try:
                    if output_dir:
                        session_file = Path(output_dir) / f"session-{username}"
                    else:
                        session_file = Path(f"session-{username}")
                    
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        L.save_session_to_file(str(session_file))
                    
                    print_info("Session saved for future use")
                except Exception as save_error:
                    print_info("Could not save session file (not critical)")
            else:
                print_error("Authentication test failed!")
                print_error("Your cookies may be expired or invalid")
                return False
                
        except Exception as e:
            print_error("Failed to load session")
            print_error(str(e)[:80])
            print_info(f"Full error: {e}")
            return False
    else:
        print_warning("Running without login")
        print_warning("Some content may be unavailable")
    
    if session_data:
        print_progress("Waiting 5 seconds to avoid rate limits...")
        time.sleep(5)
    
    try:
        # Load the profile
        print_header("PROFILE INFORMATION")
        print()
        time.sleep(4)
        print_progress(f"Loading profile: @{target_username}")
        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            profile = instaloader.Profile.from_username(L.context, target_username)
            # Access properties to trigger any lazy-loaded GraphQL requests while suppressed
            _ = profile.followers
            _ = profile.followees
            _ = profile.mediacount
            _ = profile.biography
            _ = profile.is_private
        
        print()
        print_stat("Username", f"@{profile.username}", 11)
        print_stat("Full Name", profile.full_name, 11)
        print_stat("Followers", f"{profile.followers:,}", 11)
        print_stat("Following", f"{profile.followees:,}", 11)
        print_stat("Total Posts", f"{profile.mediacount:,}", 11)
        print_stat("Private", "Yes" if profile.is_private else "No", 11)
        if profile.biography:
            bio_preview = profile.biography[:80] + "..." if len(profile.biography) > 80 else profile.biography
            print_stat("Bio", bio_preview, 11)
        
        if profile.is_private and not session_data:
            print_error("Profile is private. Login required.")
            return False
        
        # Save profile info to text file
        if profile_name:
            info_file = profile_folder / f"@{target_username}.txt"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Instagram Profile Archive\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"Username    : @{profile.username}\n")
                f.write(f"Full Name   : {profile.full_name}\n")
                f.write(f"User ID     : {profile.userid}\n")
                f.write(f"Followers   : {profile.followers:,}\n")
                f.write(f"Following   : {profile.followees:,}\n")
                f.write(f"Total Posts : {profile.mediacount:,}\n")
                f.write(f"Private     : {'Yes' if profile.is_private else 'No'}\n")
                f.write(f"Biography   : {profile.biography}\n\n")
                f.write(f"Archived on : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            id_file = profile_folder / "id"
            with open(id_file, 'w') as f:
                f.write(str(profile.userid))
        
        # Download profile picture
        print_header("DOWNLOADING CONTENT")
        print_subheader("[1/4] Profile Picture")
        try:
            if profile_name:
                existing_pics = list(profile_folder.glob("*profile_pic*"))
                if existing_pics:
                    print_info("Profile picture already exists (skipped)")
                    stats['profile_pic'] = True
                else:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        L.download_profilepic(profile)
                    
                    source_folder = Path.cwd() / target_username
                    if source_folder.exists():
                        for pic in source_folder.glob("*profile_pic*"):
                            dest = profile_folder / pic.name
                            pic.rename(dest)
                            print_success("Profile picture saved")
                            stats['profile_pic'] = True
                        try:
                            source_folder.rmdir()
                        except:
                            pass
            else:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    L.download_profilepic(profile)
                print_success("Profile picture saved")
                stats['profile_pic'] = True
        except Exception as e:
            print_warning(str(e)[:60])
            if profile_name:
                source_folder = Path.cwd() / target_username
                try:
                    if source_folder.exists():
                        source_folder.rmdir()
                except:
                    pass
        
        time.sleep(3)
        
        # Download posts with retry logic
        print_subheader("[2/4] Posts")
        retry_count = 0
        max_retries = 3
        
        print_progress("Fetching post list...")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            posts = list(profile.get_posts())
        print_info(f"Found {len(posts)} posts to download")
        print()
        
        for i, post in enumerate(posts):
            post_date = post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')
            if profile_name:
                existing = list(posts_folder.glob(f"*{post_date}*"))
                if existing:
                    stats['posts_skipped'] += 1
                    print(f"{Fore.CYAN}[{i+1}/{len(posts)}]{Style.RESET_ALL} Post already exists (skipped)")
                    continue
            
            while retry_count < max_retries:
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        L.download_post(post, target="_temp_")
                    
                    if profile_name:
                        source_folder = Path.cwd() / "_temp_"
                        if source_folder.exists():
                            for file in source_folder.iterdir():
                                if file.is_file():
                                    dest = posts_folder / file.name
                                    if dest.exists():
                                        dest.unlink()
                                    file.rename(dest)
                    
                    stats['posts_new'] += 1
                    print(f"{Fore.GREEN}[{stats['posts_new'] + stats['posts_skipped']}/{len(posts)}]{Style.RESET_ALL} Post downloaded")
                    time.sleep(3)
                    retry_count = 0
                    break
                except instaloader.exceptions.ConnectionException as e:
                    retry_count += 1
                    error_str = str(e)
                    if "429" in error_str or "wait" in error_str.lower():
                        wait_time = 60 * retry_count
                        print(f"{Fore.YELLOW}[{i+1}/{len(posts)}]{Style.RESET_ALL} Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    elif "403" in error_str or "401" in error_str:
                        wait_time = 30 * retry_count
                        print(f"{Fore.YELLOW}[{i+1}/{len(posts)}]{Style.RESET_ALL} Access error, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"{Fore.YELLOW}[{i+1}/{len(posts)}]{Style.RESET_ALL} Connection error, retrying...")
                        time.sleep(10)
                    
                    if retry_count >= max_retries:
                        print(f"{Fore.RED}[{i+1}/{len(posts)}]{Style.RESET_ALL} SKIPPED (failed after {max_retries} attempts)")
                        break
                except Exception as e:
                    print(f"{Fore.RED}[{i+1}/{len(posts)}]{Style.RESET_ALL} ERROR - {str(e)[:40]}")
                    break
        
        if profile_name:
            source_folder = Path.cwd() / "_temp_"
            try:
                if source_folder.exists() and source_folder.is_dir():
                    source_folder.rmdir()
            except:
                pass
        
        print()
        print_success(f"Downloaded {stats['posts_new']} new posts")
        if stats['posts_skipped'] > 0:
            print_info(f"Skipped {stats['posts_skipped']} posts (already exist)")
        
        # Download stories (if available)
        if session_data:
            print_subheader("[3/4] Stories")
            time.sleep(3)
            try:
                for story in L.get_stories(userids=[profile.userid]):
                    for item in story.get_items():
                        item_date = item.date_utc.strftime('%Y-%m-%d_%H-%M-%S')
                        if profile_name:
                            existing = list(stories_folder.glob(f"*{item_date}*"))
                            if existing:
                                stats['stories_skipped'] += 1
                                print_info(f"Story {stats['stories_new'] + stats['stories_skipped'] + 1}: Already exists (skipped)")
                                continue
                        
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            L.download_storyitem(item, target="_temp_")
                        
                        if profile_name:
                            source_folder = Path.cwd() / "_temp_"
                            if source_folder.exists():
                                for file in source_folder.iterdir():
                                    if file.is_file():
                                        dest = stories_folder / file.name
                                        if dest.exists():
                                            dest.unlink()
                                        file.rename(dest)
                        
                        stats['stories_new'] += 1
                        print_success(f"Story {stats['stories_new'] + stats['stories_skipped']}: Downloaded")
                        time.sleep(2)
                
                if profile_name:
                    source_folder = Path.cwd() / "_temp_"
                    try:
                        if source_folder.exists() and source_folder.is_dir():
                            source_folder.rmdir()
                    except:
                        pass
                
                if stats['stories_new'] > 0 or stats['stories_skipped'] > 0:
                    print()
                    if stats['stories_new'] > 0:
                        print_success(f"Downloaded {stats['stories_new']} new story items")
                    if stats['stories_skipped'] > 0:
                        print_info(f"Skipped {stats['stories_skipped']} items (already exist)")
                else:
                    print_info("No active stories found")
            except Exception as e:
                print_warning(f"Stories unavailable: {str(e)[:50]}")
        
        # Download highlights
        if session_data:
            print_subheader("[4/4] Highlights")
            time.sleep(3)
            try:
                highlight_sets = list(L.get_highlights(profile))
                
                if not highlight_sets:
                    print_info("No highlights found")
                else:
                    print_info(f"Found {len(highlight_sets)} highlight sets")
                    print()
                
                for idx, highlight in enumerate(highlight_sets, 1):
                    items = list(highlight.get_items())
                    highlight_title = highlight.title.strip() or f"Set {idx}"
                    
                    for item_idx, item in enumerate(items, 1):
                        item_date = item.date_utc.strftime('%Y-%m-%d_%H-%M-%S')
                        if profile_name:
                            existing = list(highlights_folder.glob(f"*{item_date}*"))
                            if existing:
                                stats['highlights_skipped'] += 1
                                print_info(f"Highlight '{highlight_title}' [{item_idx}/{len(items)}]: Already exists (skipped)")
                                continue
                        
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            L.download_storyitem(item, target="_temp_")
                        
                        if profile_name:
                            source_folder = Path.cwd() / "_temp_"
                            if source_folder.exists():
                                for file in source_folder.iterdir():
                                    if file.is_file():
                                        dest = highlights_folder / file.name
                                        if dest.exists():
                                            dest.unlink()
                                        file.rename(dest)
                        
                        stats['highlights_new'] += 1
                        print_success(f"Highlight '{highlight_title}' [{item_idx}/{len(items)}]: Downloaded")
                        time.sleep(2)
                    
                    print_info(f"'{highlight_title}' complete")
                    print()
                
                if profile_name:
                    source_folder = Path.cwd() / "_temp_"
                    try:
                        if source_folder.exists() and source_folder.is_dir():
                            source_folder.rmdir()
                    except:
                        pass
                
                if stats['highlights_new'] > 0 or stats['highlights_skipped'] > 0:
                    if stats['highlights_new'] > 0:
                        print_success(f"Downloaded {stats['highlights_new']} new highlight items total")
                    if stats['highlights_skipped'] > 0:
                        print_info(f"Skipped {stats['highlights_skipped']} items (already exist)")
            except Exception as e:
                print_warning(f"Highlights unavailable: {str(e)[:50]}")
        
        # Download tagged posts
        print_subheader("[BONUS] Tagged Posts")
        print_info("Skipped (posts where others tagged this profile)")
        
        print_header("ARCHIVE COMPLETE")
        print()
        print_stat("Target Profile", f"@{target_username}", 14)
        print_stat("Profile Pic", "Yes" if stats['profile_pic'] else "No", 14)
        print_stat("Posts", f"{stats['posts_new']} new, {stats['posts_skipped']} skipped", 14)
        print_stat("Stories", f"{stats['stories_new']} new, {stats['stories_skipped']} skipped", 14)
        print_stat("Highlights", f"{stats['highlights_new']} new, {stats['highlights_skipped']} skipped", 14)
        if profile_name:
            print_stat("Saved to", str(profile_folder), 14)
        else:
            print_stat("Location", output_dir if output_dir else "Current directory", 14)
        print()
        return True
        
    except instaloader.exceptions.ProfileNotExistsException:
        print_error(f"Profile '@{target_username}' does not exist")
        return False
    except instaloader.exceptions.ConnectionException as e:
        print_error("Connection failed")
        print_error(str(e)[:100])
        print()
        print_info("TIP: Instagram may have rate limited your account.")
        print_info("Please wait 30-60 minutes before trying again.")
        return False
    except KeyboardInterrupt:
        print()
        print_warning("Download interrupted by user")
        return False
    except Exception as e:
        print_error(str(e)[:100])
        return False


def load_config():
    """Load configuration from config.json file"""
    config_file = Path("config.json")
    
    if not config_file.exists():
        default_config = {
            "my_username": "your_username",
            "my_cookies": {
                "csrftoken": "your_csrftoken",
                "sessionid": "your_sessionid",
                "ds_user_id": "your_ds_user_id",
                "mid": "your_mid",
                "ig_did": "your_ig_did"
            },
            "download_directory": "C:\\Users\\Administrator\\Downloads\\Local Archives",
            "profiles_to_download": [
                {
                    "username": "example_username",
                    "folder_name": "Example Name"
                },
                {
                    "username": "example_username",
                    "folder_name": "Example Name"
                },
                {
                    "username": "example_username",
                    "folder_name": "Example Name"
                }
            ]
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        
        print_warning("Created default config.json file")
        print_warning("Please edit config.json to add your credentials and profiles")
        print_info(f"Location: {config_file.absolute()}")
        print()
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main function with config file support"""
    
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}+{'-' * 68}+")
    print(f"|{f'INSTAGRAM PROFILE ARCHIVER v{VERSION}'.center(68)}|")
    print(f"|{'Multiple Profiles - Config File'.center(68)}|")
    print(f"+{'-' * 68}+{Style.RESET_ALL}")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print_error("Failed to load config.json")
        print_error(str(e))
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    my_username = config.get("my_username")
    my_cookies = config.get("my_cookies")
    download_dir = config.get("download_directory")
    profiles = config.get("profiles_to_download", [])
    
    if not profiles:
        print_error("No profiles configured in config.json")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print()
    print_stat("Login Account", f"@{my_username}", 13)
    print_stat("Save Location", download_dir, 13)
    print_stat("Profiles", f"{len(profiles)} profile(s) to download", 13)
    
    # Create output directory
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    
    # Prepare session data
    session_data = {
        'username': my_username,
        'cookies': my_cookies
    }
    
    # Download each profile
    success_count = 0
    failed_count = 0
    
    for idx, profile_config in enumerate(profiles, 1):
        target_username = profile_config.get("username")
        folder_name = profile_config.get("folder_name")
        
        if not target_username or not folder_name:
            print_warning(f"Skipping invalid profile config: {profile_config}")
            failed_count += 1
            continue
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}+{'-' * 68}+")
        profile_line = f" Profile ({idx}/{len(profiles)}) : @{target_username}"
        folder_line = f" Folder        : {folder_name}"
        print(f"|{profile_line}{' ' * (68 - len(profile_line) - 1)} |")
        print(f"|{folder_line}{' ' * (68 - len(folder_line) - 1)} |")
        print(f"+{'-' * 68}+{Style.RESET_ALL}")
        
        success = archive_profile(target_username, session_data, download_dir, folder_name)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        if idx < len(profiles):
            print_progress("Waiting 10 seconds before next profile...")
            time.sleep(10)
    
    # Final summary
    print_header("FINAL SUMMARY")
    print()
    print_stat("Total Profiles", str(len(profiles)), 14)
    print_stat("Successful", str(success_count), 14)
    print_stat("Failed", str(failed_count), 14)
    print()
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()