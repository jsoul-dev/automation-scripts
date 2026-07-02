# pip install psutil cryptography

import os
import sys
import json
import time
import shutil
import urllib.request
import re
import html
from pathlib import Path
import psutil
from typing import Optional
import base64
import hashlib
import hmac
import secrets
from hashlib import pbkdf2_hmac

__version__ = "1.3.1"

# --- Stat Definitions from table.txt (Core stats only) ---
STAT_OPTIONS = {
    1: "Attack Damage",
    2: "Attack Speed",
    5: "Max HP",
    6: "Armor",
    7: "Movement Speed",
    10: "Cooldown Reduction",
    48: "Additional XP"
}

HERO_COLORS = {
    "Knight": "\033[93m",     # Yellow
    "Ranger": "\033[92m",     # Green
    "Sorcerer": "\033[95m",   # Magenta
    "Priest": "\033[96m",     # Cyan
    "Hunter": "\033[33m",     # Dark Yellow/Orange
    "Slayer": "\033[91m"      # Red
}

# UI Mapping for cleaner menu
MENU_OPTIONS = {
    1: (6, "Armor"),
    2: (5, "Max HP"),
    3: (2, "Attack Speed"),
    4: (1, "Attack Damage"),
    5: (48, "Additional XP"),
    6: (7, "Movement Speed"),
    7: (10, "Cooldown Reduction")
}

# --- Keys / Constants (Taskbar Hero v1.00.21) ---
ES3_PASSWORD = "emuMqG3bLYJ938ZDCfieWJ"   # Easy Save 3 encryption password
PBKDF2_ITERS = 100
KEY_SIZE     = 16
IV_SIZE      = 16

# HMAC-SHA256 key for the "SystemInfo" integrity field (extracted from the binary).
SYSTEMINFO_HMAC_KEY = bytes.fromhex(
    "93d9429e9b72f22fdb3413193763eaba1e8cfae995f61466a81a36a609d8e456"
)
SYSTEMINFO_SEP = "|"

# Default save location on Windows
DEFAULT_SAVE_DIR  = (
    Path(os.environ.get("USERPROFILE", Path.home()))
    / "AppData" / "LocalLow" / "TesseractStudio" / "TaskBarHero"
)
DEFAULT_SAVE_FILE = DEFAULT_SAVE_DIR / "SaveFile_Live.es3"
DEFAULT_JSON_DIR  = Path.cwd() / "tbh-save-backups"
PLAYER_JSON       = DEFAULT_JSON_DIR / "player.json"
ACCOUNT_JSON      = DEFAULT_JSON_DIR / "account.json"

# ── AES-CBC backend ───────────────────────────────────────────────────────────
# Uses 'cryptography' (fast) when available, falls back to a bundled pure-Python
# implementation (aes_pure.py) if the package is missing.

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    def _aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
        dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        return dec.update(data) + dec.finalize()

    def _aes_cbc_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
        enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        return enc.update(data) + enc.finalize()

    AES_BACKEND = "cryptography"

except ImportError:
    try:
        import aes_pure  # type: ignore  # bundled fallback in the same folder

        def _aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
            return aes_pure.cbc_decrypt(key, iv, data)

        def _aes_cbc_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
            return aes_pure.cbc_encrypt(key, iv, data)

        AES_BACKEND = "pure-python"

    except ImportError:
        print(
            "[ERROR] No AES backend available.\n"
            "Install the 'cryptography' package:  pip install cryptography"
        )
        sys.exit(1)

# ── PKCS7 padding ─────────────────────────────────────────────────────────────

def _pkcs7_pad(data: bytes, block: int = 16) -> bytes:
    n = block - (len(data) % block)
    return data + bytes([n]) * n


def _pkcs7_unpad(data: bytes) -> bytes:
    n = data[-1]
    if not (1 <= n <= 16):
        raise ValueError(f"Invalid PKCS7 padding byte: {n}")
    return data[:-n]


def _derive_key(password: str, iv: bytes) -> bytes:
    return pbkdf2_hmac("sha1", password.encode("utf-8"), iv, PBKDF2_ITERS, dklen=KEY_SIZE)

# ── ES3 encrypt / decrypt ─────────────────────────────────────────────────────

def es3_decrypt(raw: bytes, password: str = ES3_PASSWORD) -> bytes:
    """Decrypt an ES3 blob: [IV (16 B)] + [AES-CBC ciphertext]."""
    iv, ct = raw[:IV_SIZE], raw[IV_SIZE:]
    key = _derive_key(password, iv)
    return _pkcs7_unpad(_aes_cbc_decrypt(key, iv, ct))


def es3_encrypt(
    plaintext: bytes,
    password: str = ES3_PASSWORD,
    iv: Optional[bytes] = None,
) -> bytes:
    """Encrypt plaintext to an ES3 blob with a random (or supplied) IV."""
    if iv is None:
        iv = secrets.token_bytes(IV_SIZE)
    key = _derive_key(password, iv)
    return iv + _aes_cbc_encrypt(key, iv, _pkcs7_pad(plaintext))

# ── SaveFile ──────────────────────────────────────────────────────────────────

class SaveFile:
    """
    Loads and unpacks a Taskbar Hero ES3 save file.

    After loading, ``account`` and ``player`` are plain Python dicts that you
    can modify freely.  Call ``save()`` or ``to_es3_bytes()`` to re-pack them.
    """

    def __init__(self, es3_obj: dict, password: str = ES3_PASSWORD) -> None:
        self._es3     = es3_obj          # outer ES3 envelope: {key: {__type, value}}
        self.password = password
        self.account: dict = json.loads(es3_obj["AccountSaveData"]["value"])
        self.player:  dict = json.loads(es3_obj["PlayerSaveData"]["value"])

    @classmethod
    def load(cls, path: Path, password: str = ES3_PASSWORD) -> "SaveFile":
        """Read and decrypt a save file from disk."""
        raw     = path.read_bytes()
        es3_obj = json.loads(es3_decrypt(raw, password).decode("utf-8"))
        return cls(es3_obj, password)

    def _compact_json(self, obj: dict) -> str:
        """Compact JSON with no extra spaces — matches Newtonsoft's default output."""
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    def to_es3_bytes(self) -> bytes:
        """Re-pack ``account`` and ``player`` back into an encrypted ES3 blob."""
        acc   = self._compact_json(self.account)
        ply   = self._compact_json(self.player)
        steam = str(self.account.get("ownerSteamId", ""))

        # Recompute the SystemInfo HMAC so the game accepts the save.
        msg     = SYSTEMINFO_SEP.join([acc, ply, steam]).encode("utf-8")
        sysinfo = base64.b64encode(
            hmac.new(SYSTEMINFO_HMAC_KEY, msg, hashlib.sha256).digest()
        ).decode("ascii")

        self._es3["AccountSaveData"]["value"] = acc
        self._es3["PlayerSaveData"]["value"]  = ply
        self._es3["SystemInfo"]["value"]      = sysinfo

        text = json.dumps(self._es3, ensure_ascii=False, indent="\t")
        return es3_encrypt(text.encode("utf-8"), self.password)

    def save(self, path: Path, backup: bool = True) -> Path:
        """Write the save to *path*.  Creates a .bak copy first unless backup=False."""
        blob = self.to_es3_bytes()
        if backup and path.exists():
            bak = path.with_name(path.name + ".bak")
            bak.write_bytes(path.read_bytes())
        path.write_bytes(blob)
        return path

# ── CLI helpers ───────────────────────────────────────────────────────────────

def _write_json(obj: dict, dest: Path) -> None:
    dest.write_text(json.dumps(obj, indent=4, ensure_ascii=False), encoding="utf-8")


def _read_json(src: Path) -> dict:
    return json.loads(src.read_text(encoding="utf-8"))


def cmd_extract(save_path: Path, json_dir: Path) -> None:
    """Decrypt the save and write player.json + account.json."""
    if not save_path.exists():
        print(f"\n[ERROR] Save file not found:\n  {save_path}")
        print("\nTip: Open the game at least once to create a save, then try again.")
        sys.exit(1)

    json_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Reading save → {save_path}")
    save = SaveFile.load(save_path)

    player_json  = json_dir / "player.json"
    account_json = json_dir / "account.json"
    _write_json(save.player,  player_json)

def check_processes():
    running = []
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name']
            if name and name.lower() in ['taskbarhero.exe']:
                running.append(name.lower())
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return running

def fetch_item_db():
    print("[*] Establishing uplink to tbh.city item database...")
    try:
        req = urllib.request.Request("https://tbh.city/items", headers={"User-Agent": "TBH Save Editor/2.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            page_html = response.read().decode('utf-8')
        pattern = re.compile(
            r'\{\\"id\\":(\d+),\\"name\\":\{\\"en\\":\\"([^\\"]*)\\"\},'
            r'\\"icon\\":\\"([^\\"]*)\\".*?\\"grade\\":\\"([^\\"]*)\\",\\"type\\":\\"([^\\"]*)\\"'
            r'.*?\\"stat_types\\":\[(.*?)\]',
            re.DOTALL,
        )
        items = {}
        for key, name, icon, rarity, item_type, stat_blob in pattern.findall(page_html):
            items[int(key)] = {
                "Name": html.unescape(name),
                "Rarity": rarity,
            }
        return items
    except Exception as e:
        print(f"Warning: Failed to fetch item db ({e}). Rarity will default to Rare.")
        return {}

def extract_save():
    print(f"[*] Extracting save data: {DEFAULT_SAVE_FILE.name}...")
    if not DEFAULT_SAVE_FILE.exists():
        print("[-] Target save file not found in system!")
        return False
    save = SaveFile.load(DEFAULT_SAVE_FILE)
    DEFAULT_JSON_DIR.mkdir(exist_ok=True)
    with open(PLAYER_JSON, 'w', encoding='utf-8') as f:
        json.dump(save.player, f, ensure_ascii=False, indent=4)
    with open(ACCOUNT_JSON, 'w', encoding='utf-8') as f:
        json.dump(save.account, f, ensure_ascii=False, indent=4)
    print("[+] Decryption and extraction complete.")
    return True

def inject_save():
    print(f"[*] Injecting modified payload back to: {DEFAULT_SAVE_FILE.name}...")
    save = SaveFile.load(DEFAULT_SAVE_FILE)
    with open(PLAYER_JSON, 'r', encoding='utf-8') as f:
        save.player = json.load(f)
    with open(ACCOUNT_JSON, 'r', encoding='utf-8') as f:
        save.account = json.load(f)
    save.save(DEFAULT_SAVE_FILE, backup=True)
    print("[+] Injection complete! Original state backed up.")

def get_decor_slots(rarity: str) -> int:
    r = rarity.lower()
    if 'cosmic' in r or 'divine' in r or 'celestial' in r: return 6
    if 'beyond' in r: return 5
    if 'arcana' in r: return 4
    if 'immortal' in r: return 3
    if 'legendary' in r: return 2
    if 'rare' in r: return 1
    return 0

def get_rarity_color(rarity: str) -> str:
    r = rarity.lower()
    if 'cosmic' in r: return "\033[1;35m" # Bold Magenta / Deep Purple
    if 'divine' in r: return "\033[1;97m" # Bold Bright White
    if 'celestial' in r: return "\033[1;36m" # Bold Cyan
    if 'beyond' in r: return "\033[96m"   # Light Blue / Cyan
    if 'arcana' in r: return "\033[35m"   # Purple
    if 'immortal' in r: return "\033[91m" # Pink / Red
    if 'legendary' in r: return "\033[93m" # Gold / Yellow
    if 'rare' in r: return "\033[94m"     # Blue
    if 'uncommon' in r: return "\033[92m" # Green
    return "\033[97m"                     # White (Common)

def pad_line(text: str, width: int = 150) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    visible_len = len(ansi_escape.sub('', text))
    padding = " " * max(0, width - visible_len)
    return text + padding

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    version_str = f"v{__version__}"
    print(f"""
    ========================================================
    |                                                      |
    |          [ TBH: TASK BAR HERO DECORATOR ]            |
    |{version_str.center(54)}|
    ========================================================
    """)

def main():
    os.system('') # Enable ANSI colors in Windows CMD
    if os.name == 'nt':
        os.system('mode con cols=150 lines=40')
    print_banner()
    
    procs = check_processes()
    if procs:
        print(f"\n[-] ACCESS DENIED: Taskbar Hero is currently running!")
        print("[-] You must close the game completely before extracting or injecting data.")
        input("\nPress Enter to exit...")
        sys.exit(0)
    
    print("\n[+] Process scan clear. Safe to proceed.")
    if not extract_save():
        sys.exit(1)
    
    with open(PLAYER_JSON, 'r', encoding='utf-8') as f:
        player_data = json.load(f)
        
    item_db = fetch_item_db()
    
    hero_names = {101: "Knight", 201: "Ranger", 301: "Sorcerer", 401: "Priest", 501: "Hunter", 601: "Slayer"}
    slot_names = {0: "Weapon 1", 1: "Weapon 2", 2: "Helmet", 3: "Armor", 4: "Gloves/Boots", 5: "Acc 1", 6: "Acc 2", 7: "Acc 3", 8: "Acc 4", 9: "Acc 5"}
    
    equipped = []
    for hero in player_data.get('heroSaveDatas', []):
        hk = hero.get('heroKey')
        h_name = hero_names.get(hk, str(hk))
        for slot_idx, uid in enumerate(hero.get('equippedItemIds', [])):
            if uid != 0:
                equipped.append((uid, h_name, slot_names.get(slot_idx, str(slot_idx))))
                
    if not equipped:
        print("\n[-] No equipped targets found.")
        sys.exit(0)
        
    items_by_uid = {item['UniqueId']: item for item in player_data.get('itemSaveDatas', []) if 'UniqueId' in item}
    
    first_loop = True
    while True:
        if not first_loop:
            print_banner()
        first_loop = False
        
        print("\n[!] \033[93mWARNING:\033[0m DO NOT put decors on tradable items or you risk getting banned/flagged.")
        print("    This script automatically filters out unequipped items to protect your account,")
        print("    because equipped items are inherently bound/untradable and much safer to edit.")
        print("\n[*] Discovering equipped targets...\n")
        
        valid_items = []
        for uid, h_name, slot_name in equipped:
            item = items_by_uid.get(uid)
            if not item:
                continue
            ik = item.get('ItemKey')
            db_info = item_db.get(ik, {"Name": f"Unknown Item {ik}", "Rarity": "Rare"})
            name = db_info['Name']
            rarity = db_info['Rarity']
            max_decor = get_decor_slots(rarity)
            
            enchants = item.get('EnchantData', [])
            current_decors = []
            for enc in enchants:
                if enc.get("RecipeType") == 1:
                    st = enc.get("StatType")
                    val = enc.get("Value")
                    st_name = STAT_OPTIONS.get(st, f"Stat{st}")
                    
                    if st == 2: # Attack Speed
                        current_decors.append(f"{st_name} +{val / 100.0:.1f}")
                    elif st == 10: # Cooldown Reduction
                        current_decors.append(f"{st_name} +{val / 10.0:.1f}%")
                    else:
                        current_decors.append(f"{st_name} +{val}")
                    
            if max_decor > 0:
                valid_items.append({
                    'uid': uid,
                    'name': name,
                    'rarity': rarity,
                    'hero': h_name,
                    'slot': slot_name,
                    'max_decor': max_decor,
                    'item': item,
                    'current_decors': current_decors
                })
            
        for idx, obj in enumerate(valid_items):
            # True background zebra striping using ANSI padding
            bg = "\033[48;5;236m" if idx % 2 == 1 else ""
            reset = f"\033[0m{bg}" if bg else "\033[0m"
            
            hc = HERO_COLORS.get(obj['hero'], "\033[97m")
            colored_hero = f"{hc}{obj['hero']}{reset}"
            
            if obj['current_decors']:
                colored_decors = f"\033[92m{', '.join(obj['current_decors'])}{reset}"
                decor_str = f" [\033[36mCurrent:{reset} {colored_decors}]"
            else:
                decor_str = f" [\033[36mCurrent:{reset} \033[90mEMPTY{reset}]"
                
            rc = get_rarity_color(obj['rarity'])
            colored_rarity = f"{rc}{obj['rarity']}{reset}"
            prefix = f"[{idx+1}]".rjust(4)
            
            raw_line = f"{bg} {prefix} {colored_hero}'s {obj['slot']}: {obj['name']} ({colored_rarity}) - {obj['max_decor']} slots{decor_str}"
            print(pad_line(raw_line) + "\033[0m")
            
        choice = input("\n[>] Select target ID to manipulate (or 'q' to finish and inject): ")
        if choice.lower() == 'q':
            break
            
        try:
            choice_idx = int(choice) - 1
            selected = valid_items[choice_idx]
        except (ValueError, IndexError):
            print("[-] Invalid input.")
            continue
            
        if selected['max_decor'] == 0:
            print("[-] Hardware limitation: Item rarity does not support decorations.")
            continue
            
        print(f"\n[*] Target acquired: {selected['name']} ({selected['rarity']})")
        print("[!] \033[93mWARNING:\033[0m Assigning Attack Damage to defensive gear is highly suspicious.")
        
        item = selected['item']
        enchants = item.get('EnchantData', [])
        while len(enchants) < max(6, selected['max_decor']):
            enchants.append({"StatModKey": 0, "Tier": 0, "Value": 0, "RecipeType": 0, "ModType": 0, "MaterialKey": 0, "StatType": 0})
            
        for i in range(selected['max_decor']):
            print(f"\n[*] Accessing Decor Slot {i+1}...")
            ans = input(f"[?] Override slot {i+1}? (y/n) [y]: ")
            if ans.lower() == 'n':
                continue
                
            print("\n[*] Available Stat Parameters:")
            print("  0: Clear slot (Empty)")
            for menu_id, (st_key, st_name) in MENU_OPTIONS.items():
                print(f"  {menu_id}: {st_name}")
            
            stat_choice_str = input("\n[>] Enter parameter ID (0 to clear, or parameter ID): ")
            if stat_choice_str == '0':
                enchants[i] = {"StatModKey": 0, "Tier": 0, "Value": 0, "RecipeType": 0, "ModType": 0, "MaterialKey": 0, "StatType": 0}
                continue
                
            try:
                menu_choice = int(stat_choice_str)
                if menu_choice not in MENU_OPTIONS:
                    print("[-] Invalid parameter. Skipping slot.")
                    continue
                stat_type, stat_name = MENU_OPTIONS[menu_choice]
                stat_mod_key = int(f"100{stat_type}01")
            except ValueError:
                print("[-] Invalid input.")
                continue
                
            if stat_type == 2: # Attack Speed
                prompt_msg = f"[>] Enter {stat_name} value (e.g., 100 = +1.0) [1 to 1000] (Leave blank for Max): "
                min_val, max_val = 1, 1000
            elif stat_type == 10: # Cooldown Reduction
                prompt_msg = f"[>] Enter {stat_name} value (e.g., 100 = +10.0%) [1 to 1000] (Leave blank for Max): "
                min_val, max_val = 1, 1000
            elif stat_type == 7: # Movement Speed
                prompt_msg = f"[>] Enter flat stat value for {stat_name} (1000 up to 3000) (Leave blank for Max): "
                min_val, max_val = 1000, 3000
            else:
                prompt_msg = f"[>] Enter flat stat value for {stat_name} (1000 up to 9184) (Leave blank for Max): "
                min_val, max_val = 1000, 9184
                
            while True:
                val_str = input(prompt_msg).strip()
                if not val_str:
                    val = max_val
                    print(f"[*] Max value ({max_val}) automatically applied.")
                    break
                try:
                    val = int(val_str)
                    if val < min_val or val > max_val:
                        print(f"[-] \033[91mERROR:\033[0m Value out of bounds ({min_val} - {max_val}). Please enter a safe value.")
                        continue
                    break
                except ValueError:
                    print("[-] Invalid syntax. Please enter a number.")
                
            enchants[i] = {
                "RecipeType": 1,
                "StatModKey": stat_mod_key,
                "Tier": 10,
                "Value": val,
                "MaterialKey": 119002,
                "StatType": stat_type,
                "ModType": 0
            }

        item['EnchantData'] = enchants
        
        # Recalculate applied decors count
        decor_count = sum(1 for e in enchants if e.get("RecipeType") == 1)
        item['EnchantCount'] = [decor_count, 0, 0]
        item['DecorationAppliedTotalCount'] = decor_count
        
        print("\n[+] Payload constructed in memory.")
        ans_more = input("[?] Do you want to edit another item? (y/n) [y]: ")
        if ans_more.lower() == 'n':
            break
    
    backup_path = PLAYER_JSON.with_name(PLAYER_JSON.name + f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(PLAYER_JSON, backup_path)
    with open(PLAYER_JSON, 'w', encoding='utf-8') as f:
        json.dump(player_data, f, ensure_ascii=False, indent=4)
    print(f"[+] Payload saved locally (Backup: {backup_path.name})")
    
    procs = check_processes()
    if procs:
        print(f"\n[!] ALERT: Taskbar Hero was launched during edit!")
        print("[-] Aborting auto-inject to prevent corruption. Close the game and run script again to INJECT.")
    else:
        ans = input("\n[?] Ready to inject payload into game memory? (y/n) [y]: ")
        if ans.lower() != 'n':
            print("\n[*] Commencing injection sequence...")
            inject_save()
        else:
            print("\n[-] Injection aborted by user. Payload remains saved locally.")
            
    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()
