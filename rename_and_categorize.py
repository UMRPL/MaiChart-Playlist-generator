"""
rename_and_categorize.py
------------------------
Renames maimai song folders from raw IDs to human-readable names and
sorts them into genre subfolders.

Format: {raw_id}__{title}__{artist}

English title lookup:
  - Fetches the official SEGA song list (maimai.sega.jp/data/maimai_songs.json)
  - If a matching JP title has an ASCII/English equivalent in that dataset,
    uses it directly.
  - Falls back to built-in kana->romaji for anything not found.

Zero external dependencies -- uses only Python stdlib + urllib.
"""

import json
import re
import shutil
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------
# CONFIG  (edit these to your needs)
# ---------------------------------------------------------

# Where your raw song folders are
ROOT_FOLDER = "."

# Where sorted output goes  (created automatically)
OUTPUT_BASE = "songs_sorted"

# Set True to preview without touching any files
DRY_RUN = False

# Include artist name in folder?
INCLUDE_ARTIST = True

# Try to fetch English titles from SEGA's official song list
USE_ENGLISH_TITLES = True

# Local cache file so we don't hit the server every run
# Delete this file to force a refresh of the song database
EN_CACHE_FILE = "sega_songs_cache.json"

# Max chars for each name component
MAX_TITLE_LEN  = 40
MAX_ARTIST_LEN = 30

# Keep unromanizable chars (kanji etc.) instead of dropping them
KEEP_UNICODE = True

# ---------------------------------------------------------
# SEGA SONG DATABASE
# ---------------------------------------------------------

SEGA_URL = "https://maimai.sega.jp/data/maimai_songs.json"


def load_sega_db(cache_path: Path) -> dict:
    """
    Returns a dict: normalised_jp_title -> {title, artist}
    where 'title' is the best available English/romaji title.
    Uses a local cache to avoid re-fetching every run.
    Delete the cache file to force a refresh.
    """
    if cache_path.exists():
        print(f"  Loading EN title cache from {cache_path.name} ...")
        with cache_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    print(f"  Fetching song database from SEGA ...")
    try:
        req = urllib.request.Request(
            SEGA_URL,
            headers={"User-Agent": "Mozilla/5.0 maimai-playlist-tool/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"  WARNING: Could not fetch song DB ({e}). Falling back to romanizer only.")
        return {}

    db = {}
    for song in data:
        jp_title = song.get("title", "")
        artist   = song.get("artist", "")
        if not jp_title:
            continue
        # Normalise key so we can match against maidata.txt &title= values
        key = unicodedata.normalize("NFKC", jp_title).strip()
        db[key] = {"title": jp_title, "artist": artist}

    # Persist cache
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"  Cached {len(db)} songs -> {cache_path.name}")
    return db


# ---------------------------------------------------------
# ZERO-DEPENDENCY KANA -> ROMAJI  (fallback)
# ---------------------------------------------------------

DIGRAPHS = {
    "\u304d\u3083":"kya","\u304d\u3085":"kyu","\u304d\u3087":"kyo",
    "\u304e\u3083":"gya","\u304e\u3085":"gyu","\u304e\u3087":"gyo",
    "\u3057\u3083":"sha","\u3057\u3085":"shu","\u3057\u3087":"sho",
    "\u3058\u3083":"ja", "\u3058\u3085":"ju", "\u3058\u3087":"jo",
    "\u3061\u3083":"cha","\u3061\u3085":"chu","\u3061\u3087":"cho",
    "\u306b\u3083":"nya","\u306b\u3085":"nyu","\u306b\u3087":"nyo",
    "\u3072\u3083":"hya","\u3072\u3085":"hyu","\u3072\u3087":"hyo",
    "\u3073\u3083":"bya","\u3073\u3085":"byu","\u3073\u3087":"byo",
    "\u3074\u3083":"pya","\u3074\u3085":"pyu","\u3074\u3087":"pyo",
    "\u307f\u3083":"mya","\u307f\u3085":"myu","\u307f\u3087":"myo",
    "\u308a\u3083":"rya","\u308a\u3085":"ryu","\u308a\u3087":"ryo",
    "\u3075\u3041":"fa", "\u3075\u3043":"fi", "\u3075\u3047":"fe", "\u3075\u3049":"fo",
    "\u3066\u3043":"ti", "\u3067\u3043":"di", "\u3068\u3045":"tu", "\u3069\u3045":"du",
    "\u3046\u3043":"wi", "\u3046\u3047":"we", "\u3046\u3049":"wo",
    "\u3064\u3041":"tsa","\u3064\u3043":"tsi","\u3064\u3047":"tse","\u3064\u3049":"tso",
    "\u3057\u3047":"she","\u3058\u3047":"je", "\u3061\u3047":"che",
    "\u3044\u3047":"ye",
}

MONOGRAPHS = {
    "\u3042":"a","\u3044":"i","\u3046":"u","\u3048":"e","\u304a":"o",
    "\u304b":"ka","\u304d":"ki","\u304f":"ku","\u3051":"ke","\u3053":"ko",
    "\u3055":"sa","\u3057":"shi","\u3059":"su","\u305b":"se","\u305d":"so",
    "\u305f":"ta","\u3061":"chi","\u3064":"tsu","\u3066":"te","\u3068":"to",
    "\u306a":"na","\u306b":"ni","\u306c":"nu","\u306d":"ne","\u306e":"no",
    "\u306f":"ha","\u3072":"hi","\u3075":"fu","\u3078":"he","\u307b":"ho",
    "\u307e":"ma","\u307f":"mi","\u3080":"mu","\u3081":"me","\u3082":"mo",
    "\u3084":"ya","\u3086":"yu","\u3088":"yo",
    "\u3089":"ra","\u308a":"ri","\u308b":"ru","\u308c":"re","\u308d":"ro",
    "\u308f":"wa","\u3092":"wo","\u3093":"n",
    "\u304c":"ga","\u304e":"gi","\u3050":"gu","\u3052":"ge","\u3054":"go",
    "\u3056":"za","\u3058":"ji","\u305a":"zu","\u305c":"ze","\u305e":"zo",
    "\u3060":"da","\u3062":"ji","\u3065":"zu","\u3067":"de","\u3069":"do",
    "\u3070":"ba","\u3073":"bi","\u3076":"bu","\u3079":"be","\u307c":"bo",
    "\u3071":"pa","\u3074":"pi","\u3077":"pu","\u307a":"pe","\u307d":"po",
    "\u3041":"a","\u3043":"i","\u3045":"u","\u3047":"e","\u3049":"o",
    "\u3083":"ya","\u3085":"yu","\u3087":"yo",
    "\u3094":"vu",
}

VOWELS       = set("aeiou")
WIN_FORBIDDEN = set('<>:"/\\|?*')


def kata_to_hira(text: str) -> str:
    return "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in text)


def romanize_kana(text: str) -> str:
    text = kata_to_hira(unicodedata.normalize("NFKC", text or ""))
    out, i, geminate = [], 0, False
    while i < len(text):
        ch = text[i]
        if ch == "\u3063":  # small tsu (geminate)
            geminate = True; i += 1; continue
        if ch == "\u30fc":  # long vowel mark
            if out:
                last = next((c for c in reversed(out[-1]) if c in VOWELS), "")
                if last: out.append(last)
            i += 1; continue
        pair = text[i:i+2]
        if pair in DIGRAPHS:
            roma, i = DIGRAPHS[pair], i + 2
        elif ch in MONOGRAPHS:
            roma, i = MONOGRAPHS[ch], i + 1
        else:
            out.append(ch); i += 1; geminate = False; continue
        out.append((roma[0] + roma) if geminate else roma)
        geminate = False
    return "".join(out)


def safe_name(text: str, max_len: int) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = romanize_kana(text)
    cleaned = []
    for ch in text:
        if ch in WIN_FORBIDDEN or ord(ch) < 32:
            continue
        if KEEP_UNICODE or ch.isascii():
            cleaned.append(ch)
    text = "".join(cleaned)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = re.sub(r"[.]+$", "", text).strip(" _.-")
    return text[:max_len] if text else "unknown"


# ---------------------------------------------------------
# METADATA READER
# ---------------------------------------------------------

def extract_meta(maidata_path: Path):
    title = artist = genre = None
    with maidata_path.open("r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if   l.startswith("&title="):  title  = l.split("=", 1)[1]
            elif l.startswith("&artist="): artist = l.split("=", 1)[1]
            elif l.startswith("&genre="):  genre  = l.split("=", 1)[1]
    return title, artist, genre


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    root        = Path(ROOT_FOLDER).resolve()
    output_base = root / OUTPUT_BASE
    cache_path  = root / EN_CACHE_FILE

    print("=" * 62)
    print("  maimai rename & categorize")
    print("=" * 62)
    print(f"  Root          : {root}")
    print(f"  Output        : {output_base}")
    print(f"  Dry run       : {DRY_RUN}")
    print(f"  English titles: {USE_ENGLISH_TITLES}")
    print(f"  Include artist: {INCLUDE_ARTIST}")
    print()

    sega_db = {}
    if USE_ENGLISH_TITLES:
        sega_db = load_sega_db(cache_path)
        print()

    if not DRY_RUN:
        output_base.mkdir(exist_ok=True)

    song_folders = [
        d for d in sorted(root.iterdir())
        if d.is_dir() and (d / "maidata.txt").exists()
    ]
    print(f"Found {len(song_folders)} song folder(s)\n")

    results    = []
    collisions = {}
    en_hits = en_misses = 0

    for folder in song_folders:
        raw_title, raw_artist, raw_genre = extract_meta(folder / "maidata.txt")
        original_id = folder.name

        en_title = en_artist = None
        if sega_db and raw_title:
            key   = unicodedata.normalize("NFKC", raw_title).strip()
            match = sega_db.get(key)
            if match:
                db_t = match["title"]
                db_a = match["artist"]
                if all(ord(c) < 128 for c in db_t):
                    en_title = db_t
                if all(ord(c) < 128 for c in db_a):
                    en_artist = db_a

        if en_title: en_hits   += 1
        else:        en_misses += 1

        title_safe  = safe_name(en_title  or raw_title  or "unknown_title",  MAX_TITLE_LEN)
        artist_safe = safe_name(en_artist or raw_artist or "unknown_artist", MAX_ARTIST_LEN)
        genre_safe  = safe_name(raw_genre or "unknown_genre", 30)

        new_name = (
            f"{original_id}__{title_safe}__{artist_safe}"
            if INCLUDE_ARTIST else
            f"{original_id}__{title_safe}"
        )

        dest    = output_base / genre_safe / new_name
        key_str = str(dest)
        if key_str in collisions:
            collisions[key_str] += 1
            dest = dest.parent / f"{new_name}_{collisions[key_str]}"
        else:
            collisions[key_str] = 0

        tag = "[EN]" if en_title else "[~] "
        results.append((folder, dest, genre_safe, tag))

    print(f"{'DRY RUN -- ' if DRY_RUN else ''}Processing {len(results)} folder(s):\n")
    print("  [EN] = English title from SEGA DB   [~] = kana romanized fallback\n")
    print(f"  {'SRC':<30}  {'TAG':<5}  {'GENRE':<25}  DEST")
    print("  " + "-" * 108)

    moved = skipped = errors = 0

    for src, dest, genre_safe, tag in results:
        print(f"  {src.name:<30}  {tag:<5}  {genre_safe:<25}  {dest.name}")
        if DRY_RUN:
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                print(f"    ! SKIP -- already exists: {dest.name}")
                skipped += 1
                continue
            shutil.move(str(src), str(dest))
            moved += 1
        except Exception as e:
            print(f"    X ERROR: {e}")
            errors += 1

    print()
    if USE_ENGLISH_TITLES:
        total = en_hits + en_misses
        print(f"  English lookup : {en_hits}/{total} matched  ({en_misses} romanized)")
    print()
    if DRY_RUN:
        print(f"  DRY RUN -- {len(results)} folder(s) would be processed.")
        print("  Set DRY_RUN = False to apply changes.")
    else:
        print(f"  Done!  Moved: {moved}  |  Skipped: {skipped}  |  Errors: {errors}")
        if moved:
            print(f"  Output: {output_base}")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
