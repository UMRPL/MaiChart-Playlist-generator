import os
import re

ROOT_FOLDER = "."

def process_utage_charts():
    """
    Find charts with "宴" in the title and copy their &lv_2 or &lv_3 values to &lv_7
    """
    processed = 0
    skipped = 0
    
    print("Scanning for maidata.txt files with 宴 in title...\n")
    
    for root, dirs, files in os.walk(ROOT_FOLDER):
        for file in files:
            if file == "maidata.txt":
                fullpath = os.path.join(root, file)
                
                # Read the file
                with open(fullpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Check if title contains 宴
                title = None
                title_line_idx = None
                
                for idx, line in enumerate(lines):
                    if line.startswith("&title="):
                        title = line.split("=", 1)[1]
                        title_line_idx = idx
                        break
                
                if title and "宴" in title:
                    # Find &lv_2 and &lv_3 values
                    lv_2_value = None
                    lv_3_value = None
                    lv_7_line_idx = None
                    
                    for idx, line in enumerate(lines):
                        if line.startswith("&lv_2="):
                            match = re.match(r"&lv_2=(.+)", line.strip())
                            if match:
                                lv_2_value = match.group(1)
                        elif line.startswith("&lv_3="):
                            match = re.match(r"&lv_3=(.+)", line.strip())
                            if match:
                                lv_3_value = match.group(1)
                        elif line.startswith("&lv_7="):
                            lv_7_line_idx = idx
                    
                    # If there's a value in lv_2 or lv_3, copy to lv_7
                    value_to_copy = lv_2_value or lv_3_value
                    
                    if value_to_copy:
                        print(f"Found: {title}")
                        print(f"  lv_2: {lv_2_value}, lv_3: {lv_3_value}")
                        
                        if lv_7_line_idx is not None:
                            # Replace existing &lv_7
                            lines[lv_7_line_idx] = f"&lv_7={value_to_copy}"
                            print(f"  ✓ Updated &lv_7 to: {value_to_copy}")
                        else:
                            # Find where to insert &lv_7 (after &lv_6 or after &lv_3)
                            insert_idx = None
                            for idx in range(len(lines) - 1, -1, -1):
                                if lines[idx].startswith("&lv_"):
                                    insert_idx = idx + 1
                                    break
                            
                            if insert_idx:
                                lines.insert(insert_idx, f"&lv_7={value_to_copy}")
                                print(f"  ✓ Added &lv_7={value_to_copy}")
                            else:
                                print(f"  ✗ Could not find insertion point")
                                skipped += 1
                                continue
                        
                        # Write the file back
                        with open(fullpath, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(lines))
                        
                        processed += 1
                        print()
                    else:
                        print(f"Skipped: {title} (no lv_2 or lv_3 value)")
                        skipped += 1
                        print()
    
    print(f"\nProcessing complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print(f"\n✓ DONE")

if __name__ == "__main__":
    process_utage_charts()
    input("Press Enter to exit...")
