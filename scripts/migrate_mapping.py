import json
import os
import shutil

def run_migration():
    print("Starting name mapping migration to League Context format...")

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    mappings_file = os.path.join(data_dir, "name_mappings.json")
    backup_file = os.path.join(data_dir, "name_mappings_old.json")

    # Verify existing mappings
    if not os.path.exists(mappings_file):
        print(f"Error: Could not find mappings at {mappings_file}")
        return

    # Backup the file
    print(f"Creating backup at {backup_file}...")
    shutil.copy2(mappings_file, backup_file)

    # Load existing simple mappings
    with open(mappings_file, "r", encoding="utf-8") as f:
        try:
            old_mappings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing existing JSON: {e}")
            return

    # Convert format
    new_mappings = {}
    converted_count = 0
    skipped_count = 0

    for hebrew_key, value in old_mappings.items():
        if isinstance(value, str):
            new_mappings[hebrew_key] = {
                "english": value,
                "league": ""
            }
            converted_count += 1
        elif isinstance(value, dict) and "english" in value:
            # Already converted
            new_mappings[hebrew_key] = value
            skipped_count += 1
        else:
            print(f"Warning: Unexpected value format for '{hebrew_key}': {value}")
            new_mappings[hebrew_key] = value

    # Save to file
    with open(mappings_file, "w", encoding="utf-8") as f:
        json.dump(new_mappings, f, ensure_ascii=False, indent=4)

    print(f"Migration completed successfully.")
    print(f"Entries converted: {converted_count}")
    print(f"Entries skipped (already formatted): {skipped_count}")

if __name__ == "__main__":
    run_migration()
