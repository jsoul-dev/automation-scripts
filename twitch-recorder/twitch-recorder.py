#!/usr/bin/env python3
# twitch_autorecord.py
# Requires: pip install requests streamlink colorama
# Requires ffmpeg on PATH for final remux to mp4

import time
import subprocess
import os
import signal
import requests
import datetime
import sys
import configparser
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# === LOAD CONFIGURATION ===
CONFIG_FILE = "config.ini"
VERSION = "1.0.1"

def load_config():
    """Load configuration from config.ini or create default if missing."""
    config = configparser.ConfigParser()
    
    if not os.path.exists(CONFIG_FILE):
        # Create default config
        config['Twitch'] = {
            'client_id': 'your_client_id_here',
            'client_secret': 'your_client_secret_here',
            'streamer': 'target_streamer_username'
        }
        config['Recording'] = {
            'output_dir': r'E:\.Twitch Automated Recordings',
            'quality': 'best',
            'check_interval': '30',
            'grace_period': '600',
            'heartbeat_interval': '3600'
        }
        config['StreamlinkArgs'] = {
            'retry_open': '5',
            'retry_streams': '10'
        }
        
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
        print(f"{Fore.GREEN}Created default config.ini{Style.RESET_ALL}")
    
    config.read(CONFIG_FILE)
    return config

config = load_config()

CLIENT_ID = config.get('Twitch', 'client_id', fallback='')
CLIENT_SECRET = config.get('Twitch', 'client_secret', fallback='')
STREAMER = config.get('Twitch', 'streamer', fallback='')
OUTPUT_DIR = config.get('Recording', 'output_dir', fallback=r'E:\.Twitch Automated Recordings')
QUALITY = config.get('Recording', 'quality', fallback='best')
CHECK_INTERVAL = config.getint('Recording', 'check_interval', fallback=30)
GRACE_PERIOD = config.getint('Recording', 'grace_period', fallback=600)
HEARTBEAT_INTERVAL = config.getint('Recording', 'heartbeat_interval', fallback=3600)

# Build streamlink args from config
STREAMLINK_EXTRA_ARGS = []
if 'StreamlinkArgs' in config:
    for key, value in config['StreamlinkArgs'].items():
        arg_name = '--' + key.replace('_', '-')
        STREAMLINK_EXTRA_ARGS.extend([arg_name, value])

# === GLOBALS ===
access_token = None
token_expires = 0
is_recording = False
record_process = None
current_session = None

# Utility output with colors
def now_ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def print_log(level, msg, color=Fore.WHITE):
    timestamp = f"{Fore.CYAN}[{now_ts()}]{Style.RESET_ALL}"
    level_tag = f"{color}[{level}]{Style.RESET_ALL}"
    print(f"{timestamp} {level_tag} {msg}", flush=True)

def print_check(msg):
    print_log("CHECK", msg, Fore.BLUE)

def print_info(msg):
    print_log("INFO", msg, Fore.GREEN)

def print_warn(msg):
    print_log("WARN", msg, Fore.YELLOW)

def print_error(msg):
    print_log("ERROR", msg, Fore.RED)

def print_success(msg):
    print_log("SUCCESS", msg, Fore.MAGENTA)

def format_duration(seconds):
    """Format seconds into readable duration (Xh Ym)"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# ==== Twitch API helpers ====
def get_token():
    global access_token, token_expires
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    access_token = data["access_token"]
    token_expires = time.time() + data.get("expires_in", 3600) - 60
    print_info("Token acquired/renewed")

def fetch_stream_info():
    global access_token
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    params = {"user_login": STREAMER}
    try:
        r = requests.get("https://api.twitch.tv/helix/streams", headers=headers, params=params, timeout=10)
    except requests.RequestException as e:
        return {"error": "network", "exc": e}

    if r.status_code == 429:
        return {"error": "rate_limit", "headers": r.headers, "status": r.status_code}

    if 500 <= r.status_code < 600:
        return {"error": "server", "status": r.status_code, "text": r.text}

    try:
        r.raise_for_status()
    except Exception as e:
        if r.status_code == 401:
            return {"error": "auth", "status": r.status_code, "text": r.text}
        return {"error": "http", "status": r.status_code, "text": r.text}

    data = r.json().get("data", [])
    if not data:
        return None
    return data[0]

# ==== Recording helpers ====
def make_paths():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts_name = f"{STREAMER}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.ts"
    mp4_name = ts_name.rsplit(".", 1)[0] + ".mp4"
    ts_path = os.path.join(OUTPUT_DIR, ts_name)
    mp4_path = os.path.join(OUTPUT_DIR, mp4_name)
    return ts_path, mp4_path

def start_recording(stream_obj=None):
    global record_process, current_session
    ts_path, mp4_path = make_paths()
    cmd = ["streamlink"] + STREAMLINK_EXTRA_ARGS + [f"twitch.tv/{STREAMER}", QUALITY, "-o", ts_path]
    print_info(f"Starting recording -> {Fore.WHITE}{os.path.basename(ts_path)}")
    try:
        # DEVNULL prevents subprocess pipe deadlock since we don't drain the output
        record_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0
        )
    except FileNotFoundError:
        print_error("streamlink not found. Install streamlink and ensure it's on PATH")
        raise
    current_session = {
        "started_at": stream_obj.get("started_at") if stream_obj else None,
        "id": stream_obj.get("id") if stream_obj else None,
        "ts_path": ts_path,
        "mp4_path": mp4_path,
        "start_time": time.time()
    }
    return record_process

def get_video_duration(file_path):
    """Get actual video duration using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return int(float(result.stdout.strip()))
        return None
    except Exception:
        return None

def stop_recording(finalize=True):
    global record_process, current_session
    if not record_process:
        return
    
    if record_process.poll() is None:
        print_info("Stopping recording...")
        try:
            if os.name == 'nt':
                os.kill(record_process.pid, signal.CTRL_BREAK_EVENT)
            else:
                record_process.terminate()
            record_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                record_process.kill()
                record_process.wait(timeout=2)
            except Exception:
                pass
        except Exception:
            try:
                record_process.kill()
                record_process.wait(timeout=2)
            except Exception:
                pass

    record_process = None

    if current_session and finalize:
        ts = current_session.get("ts_path")
        mp4 = current_session.get("mp4_path")
        last_live_time = current_session.get("last_live_time", time.time())
        expected_duration = int(last_live_time - current_session.get("start_time", time.time()))
        
        if ts and os.path.exists(ts):
            try:
                # Remux to MP4
                ff_cmd = ["ffmpeg", "-y", "-i", ts, "-c", "copy", "-movflags", "+faststart", mp4]
                subprocess.run(ff_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Get actual video duration
                actual_duration = get_video_duration(mp4)
                
                # Calculate difference
                if actual_duration:
                    diff = expected_duration - actual_duration
                    diff_str = format_duration(abs(diff))
                    
                    if diff > 60:  # More than 1 minute lost
                        print_success(f"Recording saved -> {Fore.WHITE}{os.path.basename(mp4)}")
                        print_warn(f"Expected: {Fore.WHITE}{format_duration(expected_duration)} {Fore.YELLOW}| Actual: {Fore.WHITE}{format_duration(actual_duration)} {Fore.YELLOW}| Lost: {Fore.RED}{diff_str}")
                    else:
                        print_success(f"Recording saved -> {Fore.WHITE}{os.path.basename(mp4)} {Fore.MAGENTA}(Expected: {format_duration(expected_duration)} | Actual: {format_duration(actual_duration)})")
                else:
                    # Couldn't get duration, just show expected
                    print_success(f"Recording saved -> {Fore.WHITE}{os.path.basename(mp4)} {Fore.MAGENTA}({format_duration(expected_duration)})")
                
                try:
                    os.remove(ts)
                except Exception:
                    pass
            except FileNotFoundError:
                print_warn(f"ffmpeg not found. Recording saved as -> {Fore.WHITE}{os.path.basename(ts)}")
            except subprocess.CalledProcessError:
                print_warn(f"ffmpeg remux failed. Recording saved as -> {Fore.WHITE}{os.path.basename(ts)}")
        else:
            print_warn("No recording file found to finalize")
    
    current_session = None

# ==== main loop ====
def main():
    global access_token, token_expires, is_recording, record_process, current_session

    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}  Twitch Auto-Recorder for {Fore.WHITE}{STREAMER}{Fore.MAGENTA}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")
    
    print_info(f"Output: {Fore.WHITE}{OUTPUT_DIR}")
    print_info(f"Quality: {Fore.WHITE}{QUALITY} {Fore.GREEN}| Check: {Fore.WHITE}{CHECK_INTERVAL}s {Fore.GREEN}| Grace: {Fore.WHITE}{GRACE_PERIOD}s")
    print_info(f"Heartbeat: {Fore.WHITE}Every {HEARTBEAT_INTERVAL // 60} minutes")
    print()
    print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}\n")
    
    try:
        get_token()
    except Exception as e:
        print_error(f"Failed to get token: {e}. Will retry in loop.")
        time.sleep(5)

    backoff = 1
    disconnect_since = None
    monitoring_printed = False
    last_disconnect_print = 0

    while True:
        try:
            # Refresh token if needed
            if not access_token or time.time() > token_expires:
                try:
                    get_token()
                except Exception as e:
                    print_error(f"Token refresh failed: {e}")
                    time.sleep(min(backoff, 60))
                    backoff = min(backoff * 2, 300)
                    continue

            info = fetch_stream_info()
            
            # Handle API errors
            if isinstance(info, dict) and info.get("error"):
                err = info["error"]
                if err == "rate_limit":
                    headers = info.get("headers", {})
                    reset = headers.get("Ratelimit-Reset")
                    wait = 60
                    try:
                        if reset:
                            reset_int = int(reset)
                            if reset_int > time.time():
                                wait = max(1, reset_int - int(time.time()))
                            else:
                                wait = 1
                    except Exception:
                        pass
                    wait = min(wait, 300) # Cap at 5 minutes to prevent massive sleep bugs
                    print_warn(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                elif err == "auth":
                    print_warn("Token unauthorized (401). Forcing token refresh...")
                    token_expires = 0
                    time.sleep(min(backoff, 60))
                    backoff = min(backoff * 2, 300)
                    continue
                elif err == "network":
                    print_warn(f"Network error. Retrying in {min(backoff, 60)}s...")
                    time.sleep(min(backoff, 60))
                    backoff = min(backoff * 2, 300)
                    continue
                elif err == "server":
                    print_warn(f"Twitch API error {info.get('status')}. Retrying in {min(backoff, 60)}s...")
                    time.sleep(min(backoff, 60))
                    backoff = min(backoff * 2, 300)
                    continue
                else:
                    print_warn(f"API error. Retrying...")
                    time.sleep(min(backoff, 60))
                    backoff = min(backoff * 2, 300)
                    continue
            
            backoff = 1

            # Streamer is offline
            if info is None:
                if is_recording:
                    if disconnect_since is None:
                        disconnect_since = time.time()
                        last_disconnect_print = time.time()
                        print_check(f"{Fore.YELLOW}{STREAMER}{Fore.BLUE} disconnected. Grace period: {Fore.WHITE}{GRACE_PERIOD}s")
                    else:
                        elapsed = int(time.time() - disconnect_since)
                        if time.time() - last_disconnect_print >= 30:
                            print_check(f"Still disconnected ({Fore.WHITE}{elapsed}s{Fore.BLUE} / {Fore.WHITE}{GRACE_PERIOD}s{Fore.BLUE})")
                            last_disconnect_print = time.time()
                    
                    if (time.time() - disconnect_since) > GRACE_PERIOD:
                        print_info(f"Stream ended. Grace period exceeded")
                        stop_recording(finalize=True)
                        is_recording = False
                        disconnect_since = None
                        monitoring_printed = False
                else:
                    if not monitoring_printed:
                        print_check(f"{Fore.WHITE}{STREAMER}{Fore.BLUE} is offline. Monitoring...")
                        monitoring_printed = True
                
                time.sleep(CHECK_INTERVAL)
                continue

            # Streamer is LIVE
            stream_id = info.get("id")
            started_at = info.get("started_at")
            title = info.get("title", "No title")
            
            if not is_recording:
                print_check(f"{Fore.RED}{STREAMER}{Fore.BLUE} is {Fore.RED}LIVE{Fore.BLUE}! | {Fore.WHITE}{title}")
                try:
                    start_recording(stream_obj=info)
                    is_recording = True
                    disconnect_since = None
                    monitoring_printed = False
                    current_session["last_live_time"] = time.time()
                    current_session["last_file_size"] = 0
                    current_session["last_size_time"] = time.time()
                except Exception as e:
                    print_error(f"Failed to start recording: {e}")
                    time.sleep(5)
                    is_recording = False
            else:
                if record_process and record_process.poll() is not None:
                    print_error("Streamlink process terminated unexpectedly. Restarting...")
                    stop_recording(finalize=True)
                    is_recording = False
                    disconnect_since = None
                    continue

                current_session["last_live_time"] = time.time()
                prev_started = current_session.get("started_at") if current_session else None
                
                # Check if recording file is still growing
                ts_path = current_session.get("ts_path")
                if ts_path and os.path.exists(ts_path):
                    curr_size = os.path.getsize(ts_path)
                    last_size = current_session.get("last_file_size", 0)
                    last_size_time = current_session.get("last_size_time", time.time())
                    
                    if curr_size > last_size:
                        current_session["last_file_size"] = curr_size
                        current_session["last_size_time"] = time.time()
                    elif time.time() - last_size_time > 120:
                        print_error("Recording file size hasn't grown in 2 minutes. Restarting streamlink...")
                        stop_recording(finalize=True)
                        is_recording = False
                        disconnect_since = None
                        continue
                
                if prev_started and started_at != prev_started:
                    print_info(f"New stream detected. Finalizing previous recording...")
                    stop_recording(finalize=True)
                    is_recording = False
                    
                    print_check(f"{Fore.RED}{STREAMER}{Fore.BLUE} is {Fore.RED}LIVE{Fore.BLUE}! | {Fore.WHITE}{title}")
                    try:
                        start_recording(stream_obj=info)
                        is_recording = True
                        disconnect_since = None
                        monitoring_printed = False
                    except Exception as e:
                        print_error(f"Failed to start new recording: {e}")
                        time.sleep(5)
                        is_recording = False
                else:
                    if disconnect_since:
                        elapsed = int(time.time() - disconnect_since)
                        print_info(f"Stream reconnected after {Fore.WHITE}{elapsed}s{Fore.GREEN}. Continuing recording...")
                        disconnect_since = None
                    
                    # Print heartbeat at configured interval (default: every 60 minutes)
                    if current_session:
                        elapsed_recording = int(time.time() - current_session.get("start_time", time.time()))
                        last_hb = current_session.get("last_heartbeat_time", current_session.get("start_time", time.time()))
                        if elapsed_recording > 0 and (time.time() - last_hb >= HEARTBEAT_INTERVAL):
                            current_session["last_heartbeat_time"] = time.time()
                            duration_str = format_duration(elapsed_recording)
                            print_check(f"Recording {Fore.YELLOW}{STREAMER}{Fore.BLUE}... ({Fore.WHITE}{duration_str}{Fore.BLUE})")

            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print()  # New line after Ctrl+C
            print_warn("Ctrl+C detected. Stopping recording...")
            if is_recording:
                stop_recording(finalize=True)
                is_recording = False
            try:
                print(f"\n{Fore.CYAN}Monitoring suspended. Press Enter to resume (or Ctrl+C again to exit)...{Style.RESET_ALL}")
                input()
                monitoring_printed = False
            except KeyboardInterrupt:
                print()  # New line
                print_info("Exiting. Goodbye!")
                sys.exit(0)
                
        except Exception as e:
            import traceback
            print_error("Unexpected error:")
            print(f"{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
            print_warn("Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()