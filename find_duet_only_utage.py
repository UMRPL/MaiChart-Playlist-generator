import os
import re
import shutil

ROOT_FOLDER = "."
MOVE_TARGET_FOLDER = "_duet_only_utage"

def get_inote_keys(content):
    """Return a set of inote slot numbers present in the file (e.g. {2, 3})."""
    return set(int(m) for m in re.findall(r'&inote_(\d+)\s*=', content))

def find_duet_only_utage():
    """
    Find [宴] charts that have ONLY &inote_2 and/or &inote_3 defined.
    These are duet-only converts that cannot be played in MajData.
    Returns list of (title, chart_folder_path, inote_slots).
    """
    found = []
    total_utage = 0

    for root, dirs, files in os.walk(ROOT_FOLDER):
        # Skip the move target folder itself
        dirs[:] = [d for d in dirs if os.path.join(root, d) != os.path.abspath(MOVE_TARGET_FOLDER)]

        for file in files:
            if file != "maidata.txt":
                continue

            fullpath = os.path.join(root, file)

            with open(fullpath, 'r', encoding='utf-8') as f:
                content = f.read()

            title_match = re.search(r'^&title=(.+)$', content, re.MULTILINE)
            if not title_match:
                continue
            title = title_match.group(1).strip()
            if not title.endswith("[宴]"):
                continue

            total_utage += 1
            inote_slots = get_inote_keys(content)

            # Duet-only: has inote entries, but none outside {2, 3}
            if inote_slots and inote_slots.issubset({2, 3}):
                chart_folder = root
                found.append((title, chart_folder, sorted(inote_slots)))

    return found, total_utage

def preview(found, total_utage):
    print(f"Scanned [宴] charts total : {total_utage}")
    print(f"Duet-only charts found    : {len(found)}")
    print()

    if not found:
        print("No duet-only charts found. Nothing to do.")
        return

    print("The following charts will be moved to:")
    print(f"  {os.path.abspath(MOVE_TARGET_FOLDER)}")
    print()
    print("-" * 60)

    for i, (title, folder, slots) in enumerate(found, 1):
        slot_str = ', '.join(f'&inote_{s}' for s in slots)
        print(f"  [{i:02d}] {title}")
        print(f"        Slots : {slot_str}")
        print(f"        From  : {folder}")
        print()

    print("-" * 60)

def move_charts(found):
    moved = 0
    errors = 0

    os.makedirs(MOVE_TARGET_FOLDER, exist_ok=True)

    for title, src_folder, slots in found:
        folder_name = os.path.basename(src_folder)
        dest = os.path.join(MOVE_TARGET_FOLDER, folder_name)

        # Avoid collision: append suffix if dest already exists
        if os.path.exists(dest):
            base = dest
            counter = 1
            while os.path.exists(dest):
                dest = f"{base}_{counter}"
                counter += 1

        try:
            shutil.move(src_folder, dest)
            print(f"  ✓ Moved: {title}")
            print(f"      {src_folder}  ->  {dest}")
            moved += 1
        except Exception as e:
            print(f"  ✗ Error moving '{title}': {e}")
            errors += 1

    print()
    print(f"Moved  : {moved}")
    if errors:
        print(f"Errors : {errors}")

def main():
    print("Scanning for duet-only [宴] charts...\n")

    found, total_utage = find_duet_only_utage()
    preview(found, total_utage)

    if not found:
        return

    while True:
        answer = input("Move all listed charts? [y/N]: ").strip().lower()
        if answer in ('y', 'yes'):
            print()
            print(f"Moving {len(found)} chart(s)...\n")
            move_charts(found)
            print("\n✓ DONE")
            break
        elif answer in ('n', 'no', ''):
            print("Aborted. No files were moved.")
            break
        else:
            print("Please enter 'y' or 'n'.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
