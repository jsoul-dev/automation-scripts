import requests
import json
import mimetypes
import shutil
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

__version__ = "2.0.0"

INPUT_DIR = 'input'
OUTPUT_DIR = 'output'
src_lang = 'ja'
out_lang = 'en'
ua = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'}
uid = {}

def getUserId():
    if uid.get('cr', 0) > 0:
        return uid['user_id']
    user_id = f"temp_fp_{md5(str(dt.now().timestamp()).encode()).hexdigest()[:24]}"
    print(Fore.CYAN + f'\n[System] Generated new session ID: {user_id}')
    uid['user_id'] = user_id
    uid['cr'] = 3
    return user_id

def natural_sort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def translate(imagePath, outFolder, prefix="", slang='ja', tlang='en'):
    fn = basename(imagePath)
    mime = mimetypes.guess_type(imagePath)[0]
    
    if not mime or not mime.startswith('image'):
        return False
        
    outPath = join(outFolder, fn)
    if exists(outPath):
        if prefix:
            print(Fore.CYAN + f"\n{prefix}")
        print(Fore.YELLOW + '  Done (Skipped - already exists)')
        return True

    ses = requests.Session()
    headers = ua.copy()
    ses.get('https://www.mangatranslate.com', headers=headers)

    user_id = getUserId()
    csrf = f"{int(user_id[-24:], 16)}"
    
    if prefix:
        print(Fore.CYAN + f"\n{prefix}")

    r = ses.get(f'https://www.mangatranslate.com/api/v1/credits/get_credits/{user_id}', headers=headers, cookies={'csrftoken': csrf})
    cr = r.json().get('data', {}).get('total_credits', 0)
    uid['cr'] = cr
    if not cr:
        uid.clear()
        raise Exception('No credits on create')
        
    with open(imagePath, 'rb') as fh:
        idat = {
            'user_id': user_id,
            'task_name': dt.now().strftime('task-%Y-%m-%d-%H-%M-%S'),
            'source_language': slang, 'target_language': tlang, 'recognition_model': 'CTD',
            'font_style': 'auto', 'font_weight': 'normal', 'spacing_x': '0', 'spacing_y': '0.15',
            'text_direction_preference': 'auto', 'expected_total': '1',
            'files': json.dumps([{"index": 0, "filename": fn, "content_type": mime, "size": len(fh.read())}]),
        }
        files = {k: (None, v) for k, v in idat.items()}
        headers.update({'x-csrf-token': csrf})

        # Initialize upload
        r = ses.post('https://www.mangatranslate.com/api/v1/manga/translation/init', files=files, headers=headers, cookies={'csrftoken': csrf})
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
        uid['cr'] -= 1
        print(Fore.CYAN + '  Uploading... ', end='', flush=True)
        ses.post(uurl, data=udat, files={'file': fh}, headers=headers, cookies={'csrftoken': csrf})
        ses.post(f"https://www.mangatranslate.com/api/v1/manga/translation/{task}/upload-complete", headers=headers, cookies={'csrftoken': csrf})
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
        stat = ses.get(f"https://www.mangatranslate.com/api/v1/manga/translation-tasks/{task}/images?_={dt.now().timestamp()}")
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
            tri = ses.get(stat_data['items'][0]['translated_url'], headers=headers, timeout=30)
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
                for i, f in enumerate(files, 1):
                    # Quick check before printing to avoid spamming the console for fully completed folders
                    outPath = join(output_folder_path, basename(f))
                    if exists(outPath):
                        already_done_count += 1
                        continue
                        
                    try:
                        translate(join(folder_path, f), output_folder_path, prefix=f"[{i}/{total_files}]", slang=src_lang, tlang=out_lang)
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        print(Fore.RED + f"\nError translating {f}: {e}")
                        folder_success = False
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
