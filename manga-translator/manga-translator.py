import requests
import json
import mimetypes
import sys

# Force UTF-8 encoding for Windows console to support Japanese characters and emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import shutil
import glob
from hashlib import md5
from datetime import datetime as dt
from time import sleep
from os import mkdir, listdir, rename
from os.path import exists, join, isdir, basename

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = DummyColor()

__version__ = "2.0.4"

INPUT_DIR = 'input'
OUTPUT_DIR = 'output'
src_lang = 'ja'
out_lang = 'en'
font = 'auto'
model = 'CTD'

# === Font Options ===
# "auto"                   Automatic
# "anime_ace"              Anime Ace
# "anime_ace_3"            Anime Ace v3
# "arial_unicode"          Arial Unicode
# "comic_shanns"           Comic Shanns
# "msgothic"               MS Gothic
# "msyh"                   Microsoft YaHei
# "toneoz_tc"              ToneOZ Tsuipita TC
# "klee_one"               Klee One
# "smiley_sans_oblique"    Smiley Sans Oblique
# "noto_serif_cjk_kr"      Noto Serif CJK KR

# === Model Options ===
# "CTD"     Comic Text Detector [Advanced manga text detection with high accuracy]
# "CTD2"    Complex Text Detector [Best for complex layouts]
# "HTD"     Hybrid Text Detector [Hybrid detector for multilingual and mixed-layout text]
# "QLY"     EagleEye [Best for clean text removal and redraw-ready output]
# "default" Default OCR [Basic OCR suitable for clear text]

ua = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'}
uid = {}
usecr = {'CTD2': 2, 'HTD': 2}

def getUserId():
    if uid.get('cr', 0) >= usecr.get(model, 1):
        return uid['user_id']
    user_id = f"temp_fp_{md5(str(dt.now().timestamp()).encode()).hexdigest()[:24]}"
    print(Fore.CYAN + f'\n[System] Generated new session ID: {user_id}')
    uid['user_id'] = user_id
    uid['cr'] = 3
    return user_id

def natural_sort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def translate(imagePath, outFolder, prefix="", slang='ja', tlang='en', proxy=None):
    fn = basename(imagePath)
    mime = mimetypes.guess_type(imagePath)[0]
    
    if not mime or not mime.startswith('image'):
        return False
        
    outPath = join(outFolder, fn)
    if exists(outPath):
        if prefix:
            print(Fore.CYAN + f"\n{prefix} {fn}")
        print(Fore.YELLOW + '  Done (Skipped - already exists)')
        return True

    ses = requests.Session()
    if proxy:
        ses.proxies.update({"http": f"http://{proxy}", "https": f"http://{proxy}"})
        
    headers = ua.copy()
    ses.get('https://www.mangatranslate.com', headers=headers, timeout=15)

    user_id = getUserId()
    csrf = f"{int(user_id[-24:], 16)}"
    
    if prefix:
        print(Fore.CYAN + f"\n{prefix} {fn}")

    r = ses.get(f'https://www.mangatranslate.com/api/v1/credits/get_credits/{user_id}', headers=headers, cookies={'csrftoken': csrf}, timeout=15)
    cr = r.json().get('data', {}).get('total_credits', 0)
    uid['cr'] = cr
    if not cr:
        uid.clear()
        raise Exception('No credits on create')
        
    with open(imagePath, 'rb') as fh:
        idat = {
            'user_id': user_id,
            'task_name': dt.now().strftime('task-%Y-%m-%d-%H-%M-%S'),
            'source_language': slang, 'target_language': tlang, 'recognition_model': model,
            'font_style': font, 'font_weight': 'normal', 'spacing_x': '0', 'spacing_y': '0.15',
            'text_direction_preference': 'auto', 'expected_total': '1',
            'files': json.dumps([{"index": 0, "filename": fn, "content_type": mime, "size": len(fh.read())}]),
        }
        files = {k: (None, v) for k, v in idat.items()}
        headers.update({'x-csrf-token': csrf})

        # Initialize upload
        r = ses.post('https://www.mangatranslate.com/api/v1/manga/translation/init', files=files, headers=headers, cookies={'csrftoken': csrf}, timeout=15)
        r_data = r.json()
        if r_data.get('error'):
            e = r_data['error'].get('message', r_data['error']) if isinstance(r_data['error'], dict) else r_data['error']
            raise Exception(e)
            
        uurl = f"https://www.mangatranslate.com{r_data['upload_plan']['providers'][1]['url']}"
        task = r_data['task_id']

        udat = {
            'user_id': user_id, 'index': 0,
            'source_language': slang, 'target_language': tlang
        }
        fh.seek(0)

        # Upload
        cost = usecr.get(model, 1)
        uid['cr'] -= cost
        print(Fore.CYAN + f"  Credits ({4 - uid['cr'] - cost}/3)")
        print(Fore.CYAN + '  Uploading... ', end='', flush=True)
        ses.post(uurl, data=udat, files={'file': fh}, headers=headers, cookies={'csrftoken': csrf}, timeout=15)
        ses.post(f"https://www.mangatranslate.com/api/v1/manga/translation/{task}/upload-complete", headers=headers, cookies={'csrftoken': csrf}, timeout=15)
        print(Fore.GREEN + 'Done')
        
    status = ''
    sc = 0
    timeout_counter = 0
    while status != 'completed':
        if timeout_counter >= 300: # 5 minute timeout
            raise Exception("Timeout while waiting for translation to complete")
        sleep(1)
        timeout_counter += 1
        print(Fore.CYAN + f'\r  Status ', end='', flush=True)
        stat = ses.get(f"https://www.mangatranslate.com/api/v1/manga/translation-tasks/{task}/images?_={dt.now().timestamp()}", timeout=15)
        stat_data = stat.json()
        
        if not stat_data.get('items'):
            continue
            
        cs = stat_data['items'][0]['status']
        if cs == status:
            sc += 1
        else:
            sc = 0
            
        print(f'{cs}{"." * (sc % 4):3}', end='')
        status = cs
        if stat_data['items'][0].get('error'):
            raise Exception(stat_data['items'][0]['error'])
            
    print()
    print(Fore.CYAN + "  Downloading... ", end='', flush=True)
    for x in range(5):
        try:
            tri = ses.get(stat_data['items'][0]['translated_url'], headers=headers, timeout=15)
        except KeyboardInterrupt:
            raise
        except Exception:
            if x == 4:
                raise
            print(Fore.YELLOW + f"\r  Downloading {x+1}... ", end='', flush=True)
        else:
            break
            
    with open(outPath, 'wb') as fh:
        fh.write(tri.content)
    print(Fore.GREEN + 'Done')
    return True

if __name__ == "__main__":
    try:
        proxy_list = []
        current_proxy_index = 0
        
        # Scan for proxies
        proxy_files = glob.glob(join('proxies', '**', '*.txt'), recursive=True)
        if proxy_files:
            print(Fore.CYAN + "\nFound proxy lists:")
            for i, pfile in enumerate(proxy_files, 1):
                print(f"  [{i}] {pfile}")
            
            ans = input(Fore.YELLOW + f"Do you want to use a proxy list? (y/n/1-{len(proxy_files)}): ").strip().lower()
            if ans == 'y' or (ans.isdigit() and 1 <= int(ans) <= len(proxy_files)):
                choice = 0
                if ans.isdigit():
                    choice = int(ans) - 1
                elif len(proxy_files) > 1:
                    while True:
                        try:
                            choice = int(input(f"Enter the number of the proxy list to use (1-{len(proxy_files)}): ")) - 1
                            if 0 <= choice < len(proxy_files):
                                break
                        except ValueError:
                            pass
                
                selected_file = proxy_files[choice]
                try:
                    with open(selected_file, 'r', encoding='utf-8', errors='ignore') as pf:
                        for line in pf:
                            line = line.strip()
                            if not line or line.lower().startswith(('ip,', '"ip"')): continue
                            
                            # Handle Geonode-style CSV formats (ip is index 0, port is index 7)
                            if line.startswith('"') and '","' in line:
                                parts = line.replace('"', '').split(',')
                                if len(parts) >= 8:
                                    ip, port = parts[0], parts[7]
                                    if ip.replace('.', '').isdigit() and port.isdigit():
                                        proxy_list.append(f"{ip}:{port}")
                                        continue
                                        
                            # Standard proxy list formats (IP:PORT or user:pass@IP:PORT)
                            # Avoid lines with spaces or HTML tags to prevent loading garbage
                            if ':' in line and ' ' not in line and '<' not in line:
                                proxy_list.append(line)
                                
                    print(Fore.GREEN + f"Loaded {len(proxy_list)} proxies from {selected_file}\n")
                except Exception as e:
                    print(Fore.RED + f"Failed to load proxy list: {e}\n")

        if not exists(INPUT_DIR):
            mkdir(INPUT_DIR)
            print(Fore.GREEN + f"Created '{INPUT_DIR}' directory. Please place your manga folders inside it and run the script again.")
        if not exists(OUTPUT_DIR):
            mkdir(OUTPUT_DIR)
        
        if exists(INPUT_DIR):
            folders = [f for f in listdir(INPUT_DIR) if isdir(join(INPUT_DIR, f))]
            stats = {'processed': 0, 'skipped': 0, 'failed': 0}
            
            for folder_name in folders:
                folder_path = join(INPUT_DIR, folder_name)
                output_folder_name = f"{folder_name} [MTL]"
                output_folder_path = join(OUTPUT_DIR, output_folder_name)
                
                print(Fore.CYAN + f"\nProcessing: {folder_name}")
                if not exists(output_folder_path):
                    mkdir(output_folder_path)
                
                files = [f for f in listdir(folder_path) if '.' in f]
                files.sort(key=natural_sort_key)
                
                total_files = len(files)
                if total_files == 0:
                    print(Fore.YELLOW + "  No files found in folder.")
                    continue
                    
                folder_success = True
                already_done_count = 0
                abort_all = False
                for i, f in enumerate(files, 1):
                    # Quick check before printing to avoid spamming the console for fully completed folders
                    outPath = join(output_folder_path, basename(f))
                    if exists(outPath):
                        already_done_count += 1
                        continue
                        
                    while True:
                        current_proxy = proxy_list[current_proxy_index] if proxy_list else None
                        try:
                            translate(join(folder_path, f), output_folder_path, prefix=f"[{i}/{total_files}]", slang=src_lang, tlang=out_lang, proxy=current_proxy)
                            break
                        except KeyboardInterrupt:
                            raise
                        except Exception as e:
                            error_msg = str(e)
                            if proxy_list:
                                print(Fore.RED + f"\n  [!] Proxy {current_proxy} failed or hit rate limit.")
                                current_proxy_index += 1
                                if current_proxy_index >= len(proxy_list):
                                    print(Fore.RED + "  Exhausted all proxies! Aborting folder.")
                                    folder_success = False
                                    break
                                print(Fore.YELLOW + f"  Rotating to next proxy ({current_proxy_index}/{len(proxy_list)})...")
                            else:
                                if "Too many requests" in error_msg or "rate limit" in error_msg.lower():
                                    print(Fore.RED + f"\n  [!] Rate limit hit: {error_msg}")
                                    ans = input(Fore.YELLOW + "  Wait 60s to retry, or abort and show summary? (w/a) [default: w]: ").strip().lower()
                                    if ans == 'a':
                                        folder_success = False
                                        abort_all = True
                                        break
                                    print(Fore.YELLOW + "  Waiting 60 seconds before retrying... (Change your VPN IP now to resume instantly!)")
                                    sleep(60)
                                else:
                                    print(Fore.RED + f"\nError translating {f}: {e}")
                                    folder_success = False
                                    break
                                
                    if not folder_success:
                        break
                        
                if already_done_count == total_files:
                    print(Fore.YELLOW + f"\n  Skipped (All {total_files} images already translated)")
                    stats['skipped'] += 1
                elif folder_success:
                    print(Fore.GREEN + f"\nSuccessfully finished processing: {folder_name}")
                    stats['processed'] += 1
                else:
                    print(Fore.RED + f"\nFailed processing: {folder_name}")
                    stats['failed'] += 1
                    
                if abort_all:
                    print(Fore.YELLOW + "\nAborting further processing per user request.")
                    break
                    
            print(Fore.CYAN + "\n" + "="*30)
            print(Fore.CYAN + "Summary:")
            print(Fore.GREEN + f"  Processed: {stats['processed']}")
            print(Fore.YELLOW + f"  Skipped: {stats['skipped']}")
            if stats['failed'] > 0:
                print(Fore.RED + f"  Failed: {stats['failed']}")
            else:
                print(Fore.CYAN + f"  Failed: {stats['failed']}")
            print(Fore.CYAN + "="*30)
                
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nScript interrupted by user. Exiting gracefully...")
        
    print()
    input("Press Enter to exit...")
