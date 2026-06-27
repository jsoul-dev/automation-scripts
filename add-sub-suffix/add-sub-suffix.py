import os
import re

VERSION = "1.0.0"

# Define the language mapping: keyword(s) -> suffix
LANGUAGE_SUFFIXES = {
    'english': 'eng',
    'eng': 'eng',
    'danish': 'dan',
    'german': 'ger',
    'spanish': 'spa',
    'spanish (latin american)': 'spa',
    'french': 'fre',
    'french (canadian)': 'fre',
    'italian': 'ita',
    'dutch': 'dut',
    'norwegian': 'nor',
    'portuguese': 'por',
    'finnish': 'fin',
    'swedish': 'swe',
}

def find_language_suffix(filename):
    lower_name = filename.lower()
    for key, suffix in LANGUAGE_SUFFIXES.items():
        if key in lower_name:
            return suffix
    return None

def add_language_suffix_to_subtitles(base_dir):
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            for file in os.listdir(item_path):
                if file.endswith('.srt'):
                    file_path = os.path.join(item_path, file)
                    name_part = file[:-4]  # remove .srt
                    # Check if it already has .xxx at the end
                    if re.search(r'\.[a-z]{3}$', name_part):
                        print(f"Already has suffix: {file_path}")
                        continue
                    # Try to find a language suffix
                    suffix = find_language_suffix(file)
                    if suffix:
                        new_name = f"{name_part}.{suffix}.srt"
                        new_path = os.path.join(item_path, new_name)
                        os.rename(file_path, new_path)
                        print(f"Renamed: {file_path} -> {new_path}")
                    else:
                        print(f"No matching language for: {file_path}")

if __name__ == "__main__":
    base_directory = os.path.dirname(os.path.abspath(__file__))
    add_language_suffix_to_subtitles(base_directory)
