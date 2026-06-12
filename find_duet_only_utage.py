import os
import re

ROOT_FOLDER = "."

def get_inote_keys(content):
    """Return a set of inote slot numbers present in the file (e.g. {2, 3})."""
    return set(int(m) for m in re.findall(r'&inote_(\d+)\s*=', content))

def process_utage_charts():
    """
    Find [宴] charts that have ONLY &inote_2 and &inote_3 defined.
    These are duet-only converts that cannot be played in MajData.
    """
    found = []
    total_utage = 0

    print("Scanning for [宴] charts with only &inote_2 and &inote_3 (duet-only)...\n")

    for root, dirs, files in os.walk(ROOT_FOLDER):
        for file in files:
            if file != "maidata.txt":
                continue

            fullpath = os.path.join(root, file)

            with open(fullpath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if title ends with [宴]
            title_match = re.search(r'^&title=(.+)$', content, re.MULTILINE)
            if not title_match:
                continue
            title = title_match.group(1).strip()
            if not title.endswith("[宴]"):
                continue

            total_utage += 1
            inote_slots = get_inote_keys(content)

            # We want charts that have ONLY slots 2 and/or 3 (and no others like 4, 5, 6, 7)
            solo_slots = inote_slots - {2, 3}
            if len(inote_slots) > 0 and len(solo_slots) == 0 and inote_slots.issubset({2, 3}):
                found.append((title, fullpath, sorted(inote_slots)))
                print(f"  [DUET-ONLY] {title}")
                print(f"    Path:   {fullpath}")
                print(f"    Slots:  inote_{', inote_'.join(str(s) for s in sorted(inote_slots))}")
                print()

    print("-" * 60)
    print(f"Total [宴] charts scanned : {total_utage}")
    print(f"Duet-only charts found    : {len(found)}")

    if found:
        print("\nSummary of duet-only charts:")
        for title, path, slots in found:
            print(f"  {title}  ({path})")

    print("\n✓ DONE")
    return found

if __name__ == "__main__":
    process_utage_charts()
    input("\nPress Enter to exit...")
