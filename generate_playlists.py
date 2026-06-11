import hashlib
import base64
import os
import json

ROOT_FOLDER = "."
EXCLUDED_GENRE = "宴会場"


def md5_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(hashlib.md5(f.read()).digest()).decode('utf-8')


def extract_meta(filepath):
    genre = None
    version = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("&genre="):
                genre = line.strip().split("=", 1)[1]
            elif line.startswith("&version="):
                version = line.strip().split("=", 1)[1]

            if genre and version:
                break

    return genre, version


playlists_by_version = {}
playlists_by_genre = {}

for root, dirs, files in os.walk(ROOT_FOLDER):
    for file in files:
        if file == "maidata.txt":
            fullpath = os.path.join(root, file)

            genre, version = extract_meta(fullpath)
            if not genre or not version:
                continue

            h = md5_base64(fullpath)

            # Only add to version playlist if genre is not the excluded genre
            if genre != EXCLUDED_GENRE:
                playlists_by_version.setdefault(version, []).append(h)
            
            # Always add to genre playlist
            playlists_by_genre.setdefault(genre, []).append(h)


# save version playlists
for version, hashes in playlists_by_version.items():
    with open(f"version_{version}.json", "w", encoding="utf-8") as f:
        json.dump({
            "Name": version,
            "SongHashs": sorted(set(hashes)),
            "IsPlayList": True
        }, f, indent=2, ensure_ascii=False)


# save genre playlists
for genre, hashes in playlists_by_genre.items():
    with open(f"genre_{genre}.json", "w", encoding="utf-8") as f:
        json.dump({
            "Name": genre,
            "SongHashs": sorted(set(hashes)),
            "IsPlayList": True
        }, f, indent=2, ensure_ascii=False)

print("DONE")
