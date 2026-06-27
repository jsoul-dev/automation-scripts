#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced MKV Track Filter
Filters MKV files to keep only specified audio and subtitle languages.
Removes commentary tracks and signs/songs subtitles.
"""

import os
import re
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Iterator, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from contextlib import contextmanager

# Force UTF-8 encoding for stdout/stderr
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Third-party imports (with fallback)
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback color class
    class _Color:
        RED = CYAN = GREEN = YELLOW = ""
    class _Style:
        RESET_ALL = ""
    Fore, Style = _Color(), _Style()

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

VERSION = "1.0.0"

# ---------- CONFIG (edit here) ----------
KEEP_AUDIO_LANG = "eng"          # e.g. "eng", "kor", "jpn", "rus"
KEEP_SUB_LANG = "eng"            # e.g. "eng", "kor", "rus", "none"
OUTPUT_FOLDER = "Filtered"       # Output directory name
BACKUP_ORIGINALS = False         # Move originals to backup folder
MAX_WORKERS = 1                  # Parallel processing (be careful with I/O)
VERBOSE = False                  # Enable debug logging
DRY_RUN = False                  # Preview changes without processing
SKIP_IF_EXISTS = True            # Skip if output file already exists
REMOVE_COMMENTARY = True         # Remove commentary audio tracks
REMOVE_SIGNS_SUBS = True         # Remove signs/songs subtitle tracks
# ---------------------------------------

@dataclass
class TrackPlan:
    """Plan for which tracks to keep in the output file."""
    video_ids: List[int]
    audio_ids: List[int] 
    sub_ids: List[int]
    defaults: Dict[str, Optional[int]]
    removed_commentary: int = 0
    removed_signs: int = 0

@dataclass  
class ProcessingResult:
    """Result of processing a single file."""
    filename: str
    success: bool
    original_size: int
    new_size: int = 0
    duration: float = 0
    error_msg: str = ""
    tracks_kept: Dict[str, int] = None
    tracks_removed: Dict[str, int] = None

class MKVProcessor:
    """Main processor class for MKV files."""
    
    def __init__(self):
        self.setup_logging()
        self._print_lock = threading.Lock()
        
    def setup_logging(self):
        """Configure logging based on verbosity setting."""
        level = logging.DEBUG if VERBOSE else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()] if VERBOSE else []
        )
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def print_lock(self):
        """Thread-safe printing context manager."""
        with self._print_lock:
            yield

    def print_colored(self, color: str, prefix: str, message: str, end: str = "\n"):
        """Print colored message with thread safety and Unicode support."""
        with self.print_lock():
            try:
                if HAS_COLORAMA:
                    print(f"{color}[{prefix}]{Style.RESET_ALL} {message}", end=end, flush=True)
                else:
                    print(f"[{prefix}] {message}", end=end, flush=True)
            except UnicodeEncodeError:
                # Fallback: replace problematic characters
                safe_message = message.encode('ascii', 'replace').decode('ascii')
                if HAS_COLORAMA:
                    print(f"{color}[{prefix}]{Style.RESET_ALL} {safe_message}", end=end, flush=True)
                else:
                    print(f"[{prefix}] {safe_message}", end=end, flush=True)

    @staticmethod
    def sizeof_fmt(num: int, suffix: str = "B") -> str:
        """Convert bytes to human readable format."""
        for unit in ["", "K", "M", "G", "T"]:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} P{suffix}"

    def print_simple_progress_bar(self, percent: int, desc: str = ""):
        """Print a simple progress bar (only for single-threaded mode)."""
        percent = max(0, min(int(percent), 100))
        bar_len = 30
        filled_len = int(bar_len * percent // 100)
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        with self.print_lock():
            try:
                print(f"\r{desc}[{bar}] {percent}%", end="", flush=True)
            except UnicodeEncodeError:
                safe_desc = desc.encode('ascii', 'replace').decode('ascii')
                print(f"\r{safe_desc}[{bar}] {percent}%", end="", flush=True)

    @staticmethod
    def shorten_display(filename: str) -> str:
        """Extract meaningful display name from filename."""
        base = Path(filename).stem
        
        # Try to find season/episode pattern
        patterns = [
            r"(S\d{2}E\d{2})",           # S01E01
            r"(Season\s*\d+.*Episode\s*\d+)", # Season 1 Episode 1
            r"(\d{1,2}x\d{1,2})",        # 1x01
        ]
        
        for pattern in patterns:
            match = re.search(pattern, base, re.IGNORECASE)
            if match:
                prefix = base.split(match.group(1))[0] + match.group(1)
                return prefix[:50]  # Limit length
                
        return base[:50]  # Fallback with length limit

    @staticmethod  
    def clean_display_name(filename: str) -> str:
        """Clean filename for display."""
        # Replace underscores and dots with spaces, but preserve dashes
        cleaned = re.sub(r'[._]+', ' ', filename)
        # Normalize multiple spaces to single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    @staticmethod
    def format_time(dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%I:%M %p").lstrip("0")

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

    @staticmethod
    def is_commentary_track(track: Dict) -> bool:
        """Check if audio track is commentary."""
        props = track.get("properties", {})
        track_name = (props.get("track_name") or "").lower()
        
        # Common commentary indicators
        commentary_keywords = [
            "commentary", "comment", "comments",
            "director", "cast", "crew",
            "audio commentary", "feature commentary"
        ]
        
        return any(keyword in track_name for keyword in commentary_keywords)

    @staticmethod
    def is_signs_songs_subtitle(track: Dict) -> bool:
        """Check if subtitle track is signs/songs only."""
        props = track.get("properties", {})
        track_name = (props.get("track_name") or "").lower()
        
        # Common signs/songs indicators
        signs_keywords = [
            "signs", "sign", "songs", "song",
            "signs & songs", "signs and songs",
            "signs only", "songs only",
            "signs/songs", "forced"
        ]
        
        return any(keyword in track_name for keyword in signs_keywords)

    def run_command(self, cmd: List[str], timeout: int = 300) -> Tuple[int, str]:
        """Run command and return exit code and output with proper Unicode handling."""
        try:
            self.logger.debug(f"Running command: {' '.join(str(c) for c in cmd)}")
            
            # Set environment to use UTF-8
            env = os.environ.copy()
            if sys.platform == 'win32':
                env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of crashing
                timeout=timeout,
                env=env
            )
            return result.returncode, result.stdout
        except subprocess.TimeoutExpired:
            return 124, f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            return 127, f"Command not found: {cmd[0]}"
        except Exception as e:
            return 1, f"Command failed: {str(e)}"

    def check_mkvmerge(self) -> bool:
        """Check if mkvmerge is available."""
        code, output = self.run_command(["mkvmerge", "--version"])
        if code == 0:
            # Extract version info
            version_match = re.search(r'mkvmerge v([\d.]+)', output)
            version = version_match.group(1) if version_match else "unknown"
            self.logger.info(f"Found mkvmerge version: {version}")
            return True
        return False

    def mkvmerge_supports_feature(self, feature: str) -> bool:
        """Check if mkvmerge supports a specific feature."""
        code, output = self.run_command(["mkvmerge", "--help"])
        return code == 0 and feature in output

    def probe_file_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract metadata from MKV file with proper Unicode handling."""
        # Convert Path to string with proper encoding
        file_str = str(file_path)
        
        code, output = self.run_command(["mkvmerge", "-J", file_str])
        if code != 0:
            self.logger.error(f"Failed to probe {file_path.name}: {output}")
            return None
            
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON metadata: {e}")
            return None

    def create_track_plan(self, metadata: Dict[str, Any]) -> Optional[TrackPlan]:
        """Analyze metadata and create a plan for track selection."""
        tracks = metadata.get("tracks", [])
        if not tracks:
            return None
            
        video_ids = []
        audio_ids = []
        sub_ids = []
        removed_commentary = 0
        removed_signs = 0

        def matches_language(track: Dict, target_lang: str) -> bool:
            """Check if track matches target language."""
            if target_lang.lower() == "none":
                return False
                
            props = track.get("properties", {})
            lang = (props.get("language") or props.get("language_ietf") or "").lower()
            lang_name = (props.get("language_name") or "").lower()
            
            target_lower = target_lang.lower()
            return (lang.startswith(target_lower) or 
                   target_lower in lang_name or
                   target_lower in lang)

        # Categorize tracks
        for track in tracks:
            track_type = track.get("type")
            track_id = track.get("id")
            
            if track_type == "video":
                video_ids.append(track_id)
                
            elif track_type == "audio":
                if matches_language(track, KEEP_AUDIO_LANG):
                    # Check if it's commentary
                    if REMOVE_COMMENTARY and self.is_commentary_track(track):
                        removed_commentary += 1
                        if VERBOSE:
                            props = track.get("properties", {})
                            track_name = props.get("track_name", "")
                            self.logger.debug(f"Removing commentary track: {track_name}")
                    else:
                        audio_ids.append(track_id)
                        
            elif track_type == "subtitles":
                if matches_language(track, KEEP_SUB_LANG):
                    # Check if it's signs/songs
                    if REMOVE_SIGNS_SUBS and self.is_signs_songs_subtitle(track):
                        removed_signs += 1
                        if VERBOSE:
                            props = track.get("properties", {})
                            track_name = props.get("track_name", "")
                            self.logger.debug(f"Removing signs/songs subtitle: {track_name}")
                    else:
                        sub_ids.append(track_id)

        # Set defaults (first track of each type)
        defaults = {
            "video_default": video_ids[0] if video_ids else None,
            "audio_default": audio_ids[0] if audio_ids else None, 
            "sub_default": sub_ids[0] if sub_ids else None,
        }

        return TrackPlan(
            video_ids=video_ids,
            audio_ids=audio_ids,
            sub_ids=sub_ids,
            defaults=defaults,
            removed_commentary=removed_commentary,
            removed_signs=removed_signs
        )

    def build_mkvmerge_command(self, input_path: Path, output_path: Path, 
                             plan: TrackPlan, use_json_progress: bool, is_parallel: bool) -> List[str]:
        """Build mkvmerge command based on track plan with proper Unicode handling."""
        cmd = ["mkvmerge", "--ui-language", "en"]
        
        # Only use progress format for single-threaded mode
        if use_json_progress and not is_parallel:
            cmd.extend(["--progress-format", "json"])
            
        # Convert paths to strings - subprocess handles them properly
        cmd.extend(["-o", str(output_path)])
        
        # Video tracks
        if plan.video_ids:
            cmd.extend(["-d", ",".join(map(str, plan.video_ids))])
        else:
            cmd.extend(["-d", "0"])  # No video (shouldn't happen)
            
        # Audio tracks  
        if plan.audio_ids:
            cmd.extend(["-a", ",".join(map(str, plan.audio_ids))])
        else:
            cmd.extend(["-a", "none"])
            
        # Subtitle tracks
        if plan.sub_ids:
            cmd.extend(["-s", ",".join(map(str, plan.sub_ids))])
        else:
            cmd.extend(["-s", "none"])
            
        # Set default tracks
        all_track_ids = plan.video_ids + plan.audio_ids + plan.sub_ids
        for track_id in all_track_ids:
            is_default = track_id in plan.defaults.values()
            cmd.extend(["--default-track", f"{track_id}:{'yes' if is_default else 'no'}"])
            
        cmd.append(str(input_path))
        return cmd

    def parse_mkvmerge_progress(self, process_stdout: Iterator[str]) -> Iterator[int]:
        """Parse progress from mkvmerge output."""
        last_percent = -1
        
        for line in process_stdout:
            line = line.strip()
            
            # Try JSON format first
            if line.startswith("{") and '"percentage"' in line:
                try:
                    data = json.loads(line)
                    if "percentage" in data:
                        percent = int(float(data["percentage"]))
                        if percent != last_percent and 0 <= percent <= 100:
                            last_percent = percent
                            yield percent
                        continue
                except json.JSONDecodeError:
                    pass
                    
            # Try text format
            match = re.search(r"Progress:\s*(\d+)%", line)
            if match:
                percent = int(match.group(1))
                if percent != last_percent and 0 <= percent <= 100:
                    last_percent = percent
                    yield percent

    def process_single_file(self, input_path: Path, output_dir: Path, 
                          file_index: int, total_files: int, is_parallel: bool = False) -> ProcessingResult:
        """Process a single MKV file with proper Unicode handling."""
        start_time = datetime.now()
        result = ProcessingResult(
            filename=input_path.name,
            success=False,
            original_size=input_path.stat().st_size
        )
        
        output_path = output_dir / input_path.name
        display_name = self.clean_display_name(self.shorten_display(input_path.name))
        
        try:
            # Skip if output already exists
            if SKIP_IF_EXISTS and output_path.exists():
                self.print_colored(Fore.YELLOW, "SKIP", 
                    f"({file_index}/{total_files}) {display_name} - already exists!")
                result.success = True
                result.new_size = output_path.stat().st_size

                metadata = self.probe_file_metadata(input_path)
                if metadata:
                    plan = self.create_track_plan(metadata)
                    if plan:
                        result.tracks_kept = {
                            "video": len(plan.video_ids),
                            "audio": len(plan.audio_ids),
                            "subtitles": len(plan.sub_ids)
                        }
                        result.tracks_removed = {
                            "commentary": plan.removed_commentary,
                            "signs": plan.removed_signs
                        }
                return result
                
            # For parallel processing, just show start message
            if is_parallel:
                self.print_colored(Fore.CYAN, "START", 
                    f"({file_index}/{total_files}) Processing: {display_name}")
            else:
                self.print_colored(Fore.CYAN, "INFO", 
                    f"({file_index}/{total_files}) Processing: {display_name}")
                
            # Probe metadata
            metadata = self.probe_file_metadata(input_path)
            if not metadata:
                result.error_msg = "Failed to read metadata"
                return result
                
            # Create processing plan
            plan = self.create_track_plan(metadata)
            if not plan or not plan.video_ids:
                result.error_msg = "No video tracks found"
                return result
                
            # Check if we need to process (are we filtering anything?)
            total_tracks = len(metadata.get("tracks", []))
            kept_tracks = len(plan.video_ids) + len(plan.audio_ids) + len(plan.sub_ids)
            
            if total_tracks == kept_tracks and not DRY_RUN:
                # No filtering needed, just copy
                import shutil
                shutil.copy2(input_path, output_path)
                result.success = True
                result.new_size = result.original_size
                result.tracks_kept = {
                    "video": len(plan.video_ids),
                    "audio": len(plan.audio_ids), 
                    "subtitles": len(plan.sub_ids)
                }
                result.tracks_removed = {
                    "commentary": 0,
                    "signs": 0
                }
            else:
                if DRY_RUN:
                    dry_run_msg = (f"Would process: video={len(plan.video_ids)}, "
                                  f"audio_{KEEP_AUDIO_LANG}={len(plan.audio_ids)}, "
                                  f"subs_{KEEP_SUB_LANG}={len(plan.sub_ids)}")
                    if plan.removed_commentary > 0 or plan.removed_signs > 0:
                        dry_run_msg += f" (remove: commentary={plan.removed_commentary}, signs={plan.removed_signs})"
                    self.print_colored(Fore.YELLOW, "DRY-RUN", dry_run_msg)
                    result.success = True
                    result.new_size = result.original_size  # Estimate
                    result.tracks_removed = {
                        "commentary": plan.removed_commentary,
                        "signs": plan.removed_signs
                    }
                    return result
                    
                # Build and execute command
                use_json_progress = self.mkvmerge_supports_feature("--progress-format")
                cmd = self.build_mkvmerge_command(input_path, output_path, plan, use_json_progress, is_parallel)
                
                # Set environment for proper Unicode handling
                env = os.environ.copy()
                if sys.platform == 'win32':
                    env['PYTHONIOENCODING'] = 'utf-8'
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    env=env
                )
                
                # Show progress only for single-threaded mode
                if not is_parallel:
                    if HAS_TQDM:
                        with tqdm(total=100, desc=f"Processing", 
                                 leave=False, bar_format='{desc}:{percentage:3.0f}%|{bar:50}|') as pbar:
                            last_pct = 0
                            for pct in self.parse_mkvmerge_progress(process.stdout):
                                pbar.update(pct - last_pct)
                                last_pct = pct
                            pbar.update(100 - last_pct)
                    else:
                        for pct in self.parse_mkvmerge_progress(process.stdout):
                            self.print_simple_progress_bar(pct, f"{display_name[:20]}: ")
                        print()  # New line after progress bar
                else:
                    # For parallel mode, just consume the output without showing progress
                    for line in process.stdout:
                        pass  # Consume output to prevent blocking
                        
                process.wait()
                    
                if process.returncode == 0 and output_path.exists():
                    result.success = True
                    result.new_size = output_path.stat().st_size
                    result.tracks_kept = {
                        "video": len(plan.video_ids),
                        "audio": len(plan.audio_ids),
                        "subtitles": len(plan.sub_ids)
                    }
                    result.tracks_removed = {
                        "commentary": plan.removed_commentary,
                        "signs": plan.removed_signs
                    }
                else:
                    result.error_msg = f"mkvmerge failed with code {process.returncode}"
                    
        except Exception as e:
            result.error_msg = f"Exception: {str(e)}"
            self.logger.exception(f"Error processing {input_path.name}")
            
        finally:
            result.duration = (datetime.now() - start_time).total_seconds()
            
        return result

    def backup_original(self, file_path: Path, backup_dir: Path) -> bool:
        """Move original file to backup directory."""
        try:
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / file_path.name
            file_path.rename(backup_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup {file_path.name}: {e}")
            return False

    def run(self):
        """Main processing function."""
        # Validate environment
        if not self.check_mkvmerge():
            self.print_colored(Fore.RED, "ERROR", 
                "mkvmerge not found. Please install MKVToolNix.")
            sys.exit(1)
            
        # Setup directories
        script_dir = Path(__file__).parent
        output_dir = script_dir / OUTPUT_FOLDER
        output_dir.mkdir(exist_ok=True)
        
        if BACKUP_ORIGINALS:
            backup_dir = script_dir / "Backup"
            backup_dir.mkdir(exist_ok=True)
        
        # Find MKV files
        mkv_files = list(script_dir.glob("*.mkv"))
        if not mkv_files:
            self.print_colored(Fore.RED, "ERROR", "No MKV files found!")
            sys.exit(1)
            
        # Determine processing mode
        is_parallel = MAX_WORKERS > 1 and len(mkv_files) > 1
        
        # Print configuration
        config_msg = (f"audio={KEEP_AUDIO_LANG}, subs={KEEP_SUB_LANG}, "
                     f"mode={'parallel' if is_parallel else 'sequential'}")
        if REMOVE_COMMENTARY:
            config_msg += ", remove_commentary=yes"
        if REMOVE_SIGNS_SUBS:
            config_msg += ", remove_signs=yes"
        if DRY_RUN:
            config_msg += " [DRY RUN]"
            
        self.print_colored(Fore.CYAN, "INFO", f"Starting MKV cleanup ({config_msg})")
        self.print_colored(Fore.CYAN, "INFO", f"Found {len(mkv_files)} MKV file(s) to process!")
        
        if is_parallel:
            self.print_colored(Fore.CYAN, "INFO", f"Using {MAX_WORKERS} parallel workers (progress bars disabled)\n")
        else:
            print()
        
        # Process files
        results = []
        start_time = datetime.now()
        
        if is_parallel:
            # Parallel processing - simple output only
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(self.process_single_file, mkv_file, output_dir, 
                                  idx, len(mkv_files), True): mkv_file 
                    for idx, mkv_file in enumerate(mkv_files, 1)
                }
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    self.report_file_result(result)
        else:
            # Sequential processing with progress bars
            for idx, mkv_file in enumerate(mkv_files, 1):
                result = self.process_single_file(mkv_file, output_dir, idx, len(mkv_files), False)
                results.append(result)
                self.report_file_result(result)
                
        # Handle backups if requested
        if BACKUP_ORIGINALS and not DRY_RUN:
            successful_files = [r.filename for r in results if r.success]
            for filename in successful_files:
                original_path = script_dir / filename
                if original_path.exists():
                    self.backup_original(original_path, backup_dir)
                    
        # Print final summary
        self.print_final_summary(results, start_time)

    def report_file_result(self, result: ProcessingResult):
        """Report the result of processing a single file."""
        display_name = self.clean_display_name(self.shorten_display(result.filename))
        if result.success:
            # Main success message
            self.print_colored(Fore.GREEN, "SUCCESS", f"Processed: {display_name}")
            print("")
            
            # Follow-up info with indentation and dimmer color
            if result.tracks_kept:
                track_info = (f"-- tracks: video={result.tracks_kept['video']} | "
                            f"audio_{KEEP_AUDIO_LANG}={result.tracks_kept['audio']} | "
                            f"subs_{KEEP_SUB_LANG}={result.tracks_kept['subtitles']}")
                
                # Add removed track info if any
                if result.tracks_removed:
                    removed_parts = []
                    if result.tracks_removed.get('commentary', 0) > 0:
                        removed_parts.append(f"commentary={result.tracks_removed['commentary']}")
                    if result.tracks_removed.get('signs', 0) > 0:
                        removed_parts.append(f"signs={result.tracks_removed['signs']}")
                    if removed_parts:
                        track_info += f" (removed: {', '.join(removed_parts)})"
                
                if HAS_COLORAMA:
                    # Use dim cyan for supplementary info
                    with self.print_lock():
                        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {track_info}")
                else:
                    with self.print_lock():
                        print(f"[INFO] {track_info}")
            
            if result.new_size > 0:
                saved = result.original_size - result.new_size  
                saved_pct = (saved / result.original_size * 100) if result.original_size > 0 else 0.0
                
                size_info = (f"-- ({self.sizeof_fmt(result.original_size)} → "
                           f"{self.sizeof_fmt(result.new_size)}, "
                           f"saved {saved_pct:.1f}%)\n")
                
                if HAS_COLORAMA:
                    # Use dim cyan for supplementary info
                    with self.print_lock():
                        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {size_info}")
                else:
                    with self.print_lock():
                        print(f"[INFO] {size_info}")
        else:
            self.print_colored(Fore.RED, "ERROR", 
                f"{display_name}: {result.error_msg}")

    def print_final_summary(self, results: List[ProcessingResult], start_time: datetime):
        """Print final processing summary."""
        total_duration = (datetime.now() - start_time).total_seconds()
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        total_original = sum(r.original_size for r in results)
        total_new = sum(r.new_size for r in results if r.success and r.new_size > 0)
        
        # Count removed tracks
        total_commentary_removed = sum(r.tracks_removed.get('commentary', 0) 
                                      for r in results if r.tracks_removed)
        total_signs_removed = sum(r.tracks_removed.get('signs', 0) 
                                 for r in results if r.tracks_removed)
        
        print("" + "=" * 60)
        self.print_colored(Fore.CYAN, "SUMMARY", "Processing complete!")
        self.print_colored(Fore.CYAN, "SUMMARY", f"Files processed: {successful}/{len(results)}")
        
        if failed > 0:
            self.print_colored(Fore.YELLOW, "WARNING", f"Failed: {failed}")
            
        if total_commentary_removed > 0 or total_signs_removed > 0:
            removed_msg = "Tracks removed: "
            removed_parts = []
            if total_commentary_removed > 0:
                removed_parts.append(f"{total_commentary_removed} commentary")
            if total_signs_removed > 0:
                removed_parts.append(f"{total_signs_removed} signs/songs")
            removed_msg += ", ".join(removed_parts)
            self.print_colored(Fore.CYAN, "SUMMARY", removed_msg)
            
        if total_original > 0 and total_new > 0:
            total_saved = total_original - total_new
            saved_pct = (total_saved / total_original * 100) if total_original > 0 else 0.0
            self.print_colored(Fore.CYAN, "SUMMARY", 
                f"Total size: {self.sizeof_fmt(total_original)} → "
                f"{self.sizeof_fmt(total_new)} (saved {saved_pct:.1f}%)")
                
        self.print_colored(Fore.CYAN, "SUMMARY", 
            f"Total time: {self.format_duration(total_duration)}")
        self.print_colored(Fore.CYAN, "SUMMARY", 
            f"Output location: '{OUTPUT_FOLDER}' folder")
            
        if DRY_RUN:
            self.print_colored(Fore.YELLOW, "NOTE", "This was a dry run - no files were actually processed")
        if BACKUP_ORIGINALS and not DRY_RUN:
            self.print_colored(Fore.CYAN, "SUMMARY", "Original files moved to 'Backup' folder")
            
        print("=" * 60)

def main():
    """Entry point."""
    try:
        processor = MKVProcessor()
        processor.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[CANCELLED]{Style.RESET_ALL} Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        sys.exit(1)
    finally:
        if not VERBOSE:  # Don't wait in verbose mode (likely automated)
            input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()