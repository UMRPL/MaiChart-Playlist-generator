import hashlib
import base64
import os
import json
import re

ROOT_FOLDER = "."
EXCLUDED_GENRE = "宴会場"

# Map difficulty type index to name
DIFFICULTY_NAMES = {
    2: "Basic",
    3: "Advanced",
    4: "Expert",
    5: "Master",
    6: "Re:Master"
}


def md5_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(hashlib.md5(f.read()).digest()).decode('utf-8')


def extract_meta(filepath):
    genre = None
    version = None
    difficulties = {}  # Map difficulty type (2-6) to difficulty value

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
                    # Only collect difficulty types 2-6 (Basic through Re:Master)
                    if level_index in DIFFICULTY_NAMES and level_value:
                        difficulties[level_index] = level_value

    return genre, version, difficulties


def normalize_level(level_str):
    """Convert level string to normalized format
    Range: X.0-X.6 -> X, X.7-X.9 -> X+
    Examples: 12.4 -> 12, 12.7 -> 12+
    """
    try:
        level_float = float(level_str)
        level_int = int(level_float)
        level_decimal = level_float - level_int
        
        # If decimal part is >= 0.7, it's X+
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
playlists_by_difficulty = {}
playlists_by_level = {}
processed = 0
skipped = 0
skipped_no_meta = 0
skipped_has_utage = 0

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

            genre, version, difficulties = extract_meta(fullpath)
            if not genre or not version:
                skipped += 1
                skipped_no_meta += 1
                continue

            # Check if this file has Utage (we need to check the raw file for &lv_7)
            has_utage = False
            with open(fullpath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("&lv_7="):
                        match = re.match(r"&lv_7=(.+)", line.strip())
                        if match and match.group(1).strip():
                            has_utage = True
                            break

            if has_utage:
                skipped += 1
                skipped_has_utage += 1
                continue

            h = md5_base64(fullpath)

            # Only add to version and genre playlists if genre is NOT the excluded genre
            if genre == EXCLUDED_GENRE:
                playlists_by_genre.setdefault(genre, []).append(h)
            else:
                playlists_by_version.setdefault(version, []).append(h)
                playlists_by_genre.setdefault(genre, []).append(h)

            # Add to difficulty and level playlists for each difficulty type present
            for difficulty_type, difficulty_value in difficulties.items():
                difficulty_name = DIFFICULTY_NAMES[difficulty_type]
                playlists_by_difficulty.setdefault(difficulty_name, []).append(h)
                
                # Also add to level playlists based on the numeric value
                normalized_level = normalize_level(difficulty_value)
                if normalized_level:
                    playlists_by_level.setdefault(normalized_level, []).append(h)

print(f'\n\nProcessing complete!')
print(f"  Processed: {processed}")
print(f"  Skipped: {skipped}")
print(f"    - Missing metadata: {skipped_no_meta}")
print(f"    - Has Utage (lv_7): {skipped_has_utage}")
print(f"\nPlaylists to generate:")
print(f"  Version playlists: {len(playlists_by_version)}")
print(f"  Genre playlists: {len(playlists_by_genre)}")
print(f"  Difficulty playlists: {len(playlists_by_difficulty)}")
if playlists_by_difficulty:
    difficulty_order = ["Basic", "Advanced", "Expert", "Master", "Re:Master"]
    present_difficulties = [d for d in difficulty_order if d in playlists_by_difficulty]
    print(f"    Difficulties: {', '.join(present_difficulties)}")
print(f"  Level playlists: {len(playlists_by_level)}")
if playlists_by_level:
    print(f"    Levels: {', '.join(sorted(playlists_by_level.keys(), key=lambda x: (int(x.rstrip('+')), x.endswith('+'))))}\n")
else:
    print(f"    (none generated)\n")

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


# save difficulty playlists
print("\nGenerating difficulty playlists...")
difficulty_order = ["Basic", "Advanced", "Expert", "Master", "Re:Master"]
for difficulty_name in difficulty_order:
    if difficulty_name in playlists_by_difficulty:
        hashes = playlists_by_difficulty[difficulty_name]
        with open(f"difficulty_{difficulty_name}.json", "w", encoding="utf-8") as f:
            json.dump({
                "Name": difficulty_name,
                "SongHashs": sorted(set(hashes)),
                "IsPlayList": True
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ difficulty_{difficulty_name}.json ({len(set(hashes))} songs)")

if not playlists_by_difficulty:
    print("  (no difficulties found)")


# save level playlists
print("\nGenerating level playlists...")
if playlists_by_level:
    for level, hashes in sorted(playlists_by_level.items(), key=lambda x: (int(x[0].rstrip('+')), x[0].endswith('+'))):
        with open(f"level_{level}.json", "w", encoding="utf-8") as f:
            json.dump({
                "Name": f"Level {level}",
                "SongHashs": sorted(set(hashes)),
                "IsPlayList": True
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ level_{level}.json ({len(set(hashes))} songs)")
else:
    print("  (no levels found)")

print("\n✓ DONE")
input("Press Enter to exit...")
