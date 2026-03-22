import json
import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

NAME_MAPPINGS_FILE = DATA_DIR / "name_mappings.json"
PENDING_MAPPINGS_FILE = DATA_DIR / "pending_mappings.json"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    if not PENDING_MAPPINGS_FILE.exists():
        print(f"No pending mappings found. ({PENDING_MAPPINGS_FILE} is missing)")
        return
        
    if not NAME_MAPPINGS_FILE.exists():
        verified_mappings = {}
    else:
        with open(NAME_MAPPINGS_FILE, "r", encoding="utf-8") as f:
            verified_mappings = json.load(f)
            
    with open(PENDING_MAPPINGS_FILE, "r", encoding="utf-8") as f:
        pending_mappings = json.load(f)
        
    if not pending_mappings:
        print("No pending mappings to review! You're all caught up.")
        return
        
    def get_priority(k):
        v = pending_mappings[k]
        src = v.get("source", "") if isinstance(v, dict) else ""
        if src == "Unibet Inference": return 4
        elif src == "Pinnacle Inference": return 3
        elif src == "Translated": return 2
        return 1

    keys_to_review = list(pending_mappings.keys())
    keys_to_review.sort(key=get_priority, reverse=True)
    
    print(f"Found {len(keys_to_review)} pending mappings to review.")
    input("Press Enter to begin reviewing... ")
    
    processed_count = 0
    approved_count = 0
    
    try:
        for hebrew_key in keys_to_review:
            clear_screen()
            val = pending_mappings[hebrew_key]
            
            english_name = val
            source = "Unknown"
            if isinstance(val, dict):
                english_name = val.get("english_name", "")
                source = val.get("source", "Unknown")
                
            print(f"=== Name Mapping Review ===")
            print(f"Progress: {processed_count}/{len(keys_to_review)}")
            print("-" * 30)
            print(f"Hebrew Name : {hebrew_key}")
            print(f"Suggested   : {english_name}")
            print(f"Source      : {source}")
            print("-" * 30)
            print("[A]ccept exactly as suggested")
            print("[E]dit the suggested name")
            print("[R]eject (maps to empty string to ignore in future)")
            print("[D]elete from pending (will try to infer again later)")
            print("[S]kip for now")
            print("[Q]uit and save")
            print("-" * 30)
            
            choice = input("Your choice (A/E/R/D/S/Q): ").strip().upper()
            
            if choice == 'A':
                verified_mappings[hebrew_key] = english_name
                del pending_mappings[hebrew_key]
                approved_count += 1
            elif choice == 'E':
                new_name = input("Enter correct English name: ").strip()
                if new_name:
                    verified_mappings[hebrew_key] = new_name
                    del pending_mappings[hebrew_key]
                    approved_count += 1
                else:
                    print("Empty name provided, skipping...")
                    input("Press Enter...")
            elif choice == 'R':
                verified_mappings[hebrew_key] = ""
                del pending_mappings[hebrew_key]
                approved_count += 1
            elif choice == 'D':
                del pending_mappings[hebrew_key]
                print("Deleted from pending list.")
            elif choice == 'Q':
                break
            # IF 'S', do nothing and continue
            
            processed_count += 1
            
    except KeyboardInterrupt:
        print("\nReview interrupted by user.")
        
    # Save the files
    print("\nSaving your progress...")
    
    with open(NAME_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(verified_mappings, f, ensure_ascii=False, indent=4)
        
    with open(PENDING_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(pending_mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Complete! Added/Modified {approved_count} verified mappings.")
    print(f"{len(pending_mappings)} items remaining in pending.")

if __name__ == "__main__":
    main()
