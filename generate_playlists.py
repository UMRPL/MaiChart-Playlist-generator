import hashlib
import base64
import os
import json
import re

ROOT_FOLDER = "."
EXCLUDED_GENRE = "宴会場"


def md5_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(hashlib.md5(f.read()).digest()).decode('utf-8')


def extract_meta(filepath):
    genre = None
    version = None
    levels = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("&genre="):
                genre = line.strip().split("=", 1)[1]
            elif line.startswith("&version="):
                version = line.strip().split("=", 1)[1]
            elif line.startswith("&lv_"):
                match = re.match(r"&lv_(\d)=(.+)", line.strip())
                if match:
                    level_index = int(match.group(1))
                    level_value = match.group(2).strip()
                    if level_value:  # Only if level is not empty
                        levels.append((level_index, level_value))

            if genre and version:
                break

    return genre, version, levels


def normalize_level(level_str):
    """Convert level string to normalized format (e.g., '13.8' -> '13+', '14.0' -> '14')"""
    try:
        level_float = float(level_str)
        level_int = int(level_float)
        level_decimal = level_float - level_int
        
        # If decimal part is >= 0.7, it's the next level +
        if level_decimal >= 0.7:
            return f"{level_int}+"
        else:
            return str(level_int)
    except ValueError:
        return None


# First pass: count total maidata.txt files
print("Scanning for maidata.txt files...")
total_files = 0
for root, dirs, files in os.walk(ROOT_FOLDER):
    for file in files:
        if file == "maidata.txt":
            total_files += 1

print(f"Found {total_files} maidata.txt files\n")

playlists_by_version = {}
playlists_by_genre = {}
playlists_by_level = {}
processed = 0
skipped = 0

# Second pass: process files
print("Processing files:")
for root, dirs, files in os.walk(ROOT_FOLDER):
    for file in files:
        if file == "maidata.txt":
            processed += 1
            fullpath = os.path.join(root, file)

            # Progress bar
            progress = processed / total_files
            bar_length = 30
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r[{bar}] {processed}/{total_files}', end='', flush=True)

            genre, version, levels = extract_meta(fullpath)
            if not genre or not version:
                skipped += 1
                continue

            # Skip if has level 7 (Utage)
            if any(level_index == 7 for level_index, _ in levels):
                skipped += 1
                continue

            h = md5_base64(fullpath)

            # Only add to version and genre playlists if genre is the excluded genre
            if genre == EXCLUDED_GENRE:
                playlists_by_genre.setdefault(genre, []).append(h)
            else:
                playlists_by_version.setdefault(version, []).append(h)
                playlists_by_genre.setdefault(genre, []).append(h)

            # Add to level playlists for all non-empty levels
            for level_index, level_value in levels:
                normalized_level = normalize_level(level_value)
                if normalized_level:
                    playlists_by_level.setdefault(normalized_level, []).append(h)

print(f'\n\nProcessing complete! (Skipped: {skipped})\n')

# save version playlists
print("Generating version playlists...")
for version, hashes in playlists_by_version.items():
    with open(f"version_{version}.json", "w", encoding="utf-8") as f:
        json.dump({
            "Name": version,
            "SongHashs": sorted(set(hashes)),
            "IsPlayList": True
        }, f, indent=2, ensure_ascii=False)
    print(f"  ✓ version_{version}.json ({len(set(hashes))} songs)")


# save genre playlists
print("\nGenerating genre playlists...")
for genre, hashes in playlists_by_genre.items():
    with open(f"genre_{genre}.json", "w", encoding="utf-8") as f:
        json.dump({
            "Name": genre,
            "SongHashs": sorted(set(hashes)),
            "IsPlayList": True
        }, f, indent=2, ensure_ascii=False)
    print(f"  ✓ genre_{genre}.json ({len(set(hashes))} songs)")


# save level playlists
print("\nGenerating level playlists...")
for level, hashes in sorted(playlists_by_level.items(), key=lambda x: (int(x[0].rstrip('+')), x[0].endswith('+'))):
    with open(f"level_{level}.json", "w", encoding="utf-8") as f:
        json.dump({
            "Name": f"Level {level}",
            "SongHashs": sorted(set(hashes)),
            "IsPlayList": True
        }, f, indent=2, ensure_ascii=False)
    print(f"  ✓ level_{level}.json ({len(set(hashes))} songs)")

print("\n✓ DONE")
