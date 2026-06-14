import os
import re
import shutil
from pathlib import Path

# pip install pykakasi
try:
    import pykakasi
except ImportError:
    print("ERROR: pykakasi not installed. Run: pip install pykakasi")
    exit(1)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

# Root folder where all song folders live (same as in generate_playlists.py)
ROOT_FOLDER = "."

# Maximum characters per component in the renamed folder
MAX_TITLE_LEN  = 40
MAX_ARTIST_LEN = 30

# Dry-run mode: set to True to preview changes without actually moving anything
DRY_RUN = False

# Whether to include artist in folder name
INCLUDE_ARTIST = True

# Subfolder to put genre category folders into (set to "." to put them in ROOT_FOLDER)
OUTPUT_BASE = "songs_sorted"

# ─────────────────────────────────────────
# ROMANIZER SETUP
# ─────────────────────────────────────────

kks = pykakasi.kakasi()

def romanize(text: str) -> str:
    """Convert Japanese (kanji/kana) and ASCII text to romaji using pykakasi.
    Falls back gracefully for already-latin strings."""
    if not text:
        return "unknown"
    result = kks.convert(text)
    parts = []
    for item in result:
        chunk = item.get("hepburn") or item.get("orig") or ""
        parts.append(chunk)
    return "".join(parts)

def safe_folder_name(text: str, max_len: int = 40) -> str:
    """Romanize text and strip characters not safe for folder names."""
    romanized = romanize(text)
    clean = re.sub(r"[^\w\s\-]", "", romanized, flags=re.ASCII)
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    return clean[:max_len] if clean else "unknown"

# ─────────────────────────────────────────
# METADATA READER (reuses logic from generate_playlists.py)
# ─────────────────────────────────────────

def extract_meta(maidata_path: str):
    """Return (title, artist, genre) from maidata.txt"""
    title = artist = genre = None
    with open(maidata_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("&title="):
                title  = line.split("=", 1)[1]
            elif line.startswith("&artist="):
                artist = line.split("=", 1)[1]
            elif line.startswith("&genre="):
                genre  = line.split("=", 1)[1]
    return title, artist, genre

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    root = Path(ROOT_FOLDER).resolve()
    output_base = root / OUTPUT_BASE

    if not DRY_RUN:
        output_base.mkdir(exist_ok=True)

    print(f"Root folder   : {root}")
    print(f"Output base   : {output_base}")
    print(f"Dry run       : {DRY_RUN}")
    print(f"Include artist: {INCLUDE_ARTIST}")
    print()

    # Find all direct children of root that contain maidata.txt
    song_folders = []
    for item in sorted(root.iterdir()):
        if item.is_dir() and (item / "maidata.txt").exists():
            song_folders.append(item)

    print(f"Found {len(song_folders)} song folder(s) with maidata.txt\n")

    results    = []
    collisions = {}  # dest_str -> count (to handle duplicate romanized names)

    for folder in song_folders:
        maidata = folder / "maidata.txt"
        title, artist, genre = extract_meta(str(maidata))

        original_id = folder.name  # keep the raw folder name (e.g. "0001234") as prefix

        title_safe  = safe_folder_name(title  or "unknown_title",  MAX_TITLE_LEN)
        artist_safe = safe_folder_name(artist or "unknown_artist", MAX_ARTIST_LEN)
        genre_safe  = safe_folder_name(genre  or "unknown_genre",  30)

        # Build new folder name: <original_id>__<title>[__<artist>]
        if INCLUDE_ARTIST:
            new_name = f"{original_id}__{title_safe}__{artist_safe}"
        else:
            new_name = f"{original_id}__{title_safe}"

        genre_dir = output_base / genre_safe
        dest      = genre_dir / new_name

        # Collision guard (shouldn't happen since original_id is unique, but just in case)
        dest_key = str(dest)
        if dest_key in collisions:
            collisions[dest_key] += 1
            dest = genre_dir / f"{new_name}_{collisions[dest_key]}"
        else:
            collisions[dest_key] = 0

        results.append((folder, dest, genre_safe, new_name, title, artist, genre))

    # ── Preview / Execute ──────────────────
    print(f"{'DRY RUN — ' if DRY_RUN else ''}Renaming & categorizing {len(results)} folder(s):\n")
    print(f"  {'SOURCE':<30}  {'GENRE FOLDER':<25}  DEST NAME")
    print("  " + "-" * 100)

    moved = skipped = errors = 0

    for src, dest, genre_safe, new_name, title, artist, genre in results:
        print(f"  {src.name:<30}  {genre_safe:<25}  {dest.name}")

        if DRY_RUN:
            continue

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                print(f"    ⚠ SKIP — destination already exists: {dest}")
                skipped += 1
                continue

            shutil.move(str(src), str(dest))
            moved += 1

        except Exception as e:
            print(f"    ✗ ERROR moving {src.name}: {e}")
            errors += 1

    # ── Summary ───────────────────────────
    print()
    if DRY_RUN:
        print(f"DRY RUN complete — {len(results)} folder(s) would be processed.")
        print("Set DRY_RUN = False at the top of the script to apply changes.")
    else:
        print(f"Done! Moved: {moved}  |  Skipped: {skipped}  |  Errors: {errors}")
        if moved:
            print(f"All sorted folders are in: {output_base}")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
