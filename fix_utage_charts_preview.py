import os
import re

ROOT_FOLDER = "."

def find_utage_charts():
    """
    Find charts with "宴" in the title and list them before making changes
    """
    utage_charts = []
    
    print("Scanning for maidata.txt files with 宴 in title...\n")
    
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for file in files:
            if file == "maidata.txt":
                fullpath = os.path.join(root, file)
                
                # Read the file
                with open(fullpath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Check if title contains 宴
                title = None
                lv_2_value = None
                lv_3_value = None
                has_lv_7 = False
                
                for line in lines:
                    if line.startswith("&title="):
                        title = line.split("=", 1)[1].strip()
                    elif line.startswith("&lv_2="):
                        match = re.match(r"&lv_2=(.+)", line.strip())
                        if match:
                            lv_2_value = match.group(1)
                    elif line.startswith("&lv_3="):
                        match = re.match(r"&lv_3=(.+)", line.strip())
                        if match:
                            lv_3_value = match.group(1)
                    elif line.startswith("&lv_7="):
                        match = re.match(r"&lv_7=(.+)", line.strip())
                        if match and match.group(1).strip():
                            has_lv_7 = True
                
                if title and "宴" in title:
                    value_to_copy = lv_2_value or lv_3_value
                    
                    if value_to_copy:
                        utage_charts.append({
                            'path': fullpath,
                            'title': title,
                            'lv_2': lv_2_value,
                            'lv_3': lv_3_value,
                            'has_lv_7': has_lv_7,
                            'value_to_copy': value_to_copy
                        })
    
    return utage_charts

def main():
    print("=" * 80)
    print("UTAGE CHART FIXER - PREVIEW MODE")
    print("=" * 80)
    print()
    
    utage_charts = find_utage_charts()
    
    if not utage_charts:
        print("No charts with 宴 in title found.\n")
        return
    
    print(f"Found {len(utage_charts)} chart(s) with 宴 in title:\n")
    print("-" * 80)
    
    for i, chart in enumerate(utage_charts, 1):
        print(f"{i}. {chart['title']}")
        print(f"   Path: {chart['path']}")
        print(f"   lv_2: {chart['lv_2']}")
        print(f"   lv_3: {chart['lv_3']}")
        print(f"   Current lv_7: {'EXISTS' if chart['has_lv_7'] else 'MISSING'}")
        print(f"   → Will set lv_7 to: {chart['value_to_copy']}")
        print()
    
    print("-" * 80)
    print(f"\nTotal charts to update: {len(utage_charts)}")
    print("\nPlease verify the list above.")
    print("If correct, run fix_utage_charts_apply.py to apply the changes.")
    print()

if __name__ == "__main__":
    main()
    input("Press Enter to exit...")
