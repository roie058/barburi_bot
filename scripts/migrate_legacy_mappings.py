import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

NAME_MAPPINGS_FILE = DATA_DIR / "name_mappings.json"
REVERSE_UNIBET_FILE = DATA_DIR / "reverse_unibet_teams.json"
PENDING_MAPPINGS_FILE = DATA_DIR / "pending_mappings.json"

def migrate_legacy():
    # Load reverse_unibet_teams.json for the keys to migrate
    if REVERSE_UNIBET_FILE.exists():
        with open(REVERSE_UNIBET_FILE, "r", encoding="utf-8") as f:
            unverified_keys = json.load(f)
    else:
        print(f"File not found: {REVERSE_UNIBET_FILE}")
        return

    # Load main name_mappings.json
    if NAME_MAPPINGS_FILE.exists():
        with open(NAME_MAPPINGS_FILE, "r", encoding="utf-8") as f:
            name_mappings = json.load(f)
    else:
        print(f"File not found: {NAME_MAPPINGS_FILE}")
        return

    pending_mappings = {}

    migrated_count = 0
    # Iterate through reverse unibet keys. They represent unverified translations.
    for hebrew_key in unverified_keys.keys():
        if hebrew_key in name_mappings:
            # Get the current translated/mapped English name
            english_name = name_mappings[hebrew_key]
            
            # Move to pending
            pending_mappings[hebrew_key] = {
                "english_name": english_name,
                "source": "Legacy Unverified"
            }
            
            # Remove from verified
            del name_mappings[hebrew_key]
            migrated_count += 1
            
    # Save the new verified mappings back
    with open(NAME_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(name_mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Removed {migrated_count} unverified mappings from {NAME_MAPPINGS_FILE.name}")
        
    # Merge into pending_mappings.json (if it exists)
    if PENDING_MAPPINGS_FILE.exists():
        with open(PENDING_MAPPINGS_FILE, "r", encoding="utf-8") as f:
            existing_pending = json.load(f)
        existing_pending.update(pending_mappings)
        pending_mappings = existing_pending
        
    # Save pending mappings
    with open(PENDING_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(pending_mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Saved {len(pending_mappings)} mappings to {PENDING_MAPPINGS_FILE.name}")


if __name__ == "__main__":
    migrate_legacy()
