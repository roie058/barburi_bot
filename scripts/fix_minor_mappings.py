
import json
import os

path = "data/name_mappings.json"
with open(path, "r", encoding="utf-8") as f:
    mappings = json.load(f)

# Updates
mappings["אמיין"] = "Amiens SC" # Was "Amiens"
mappings["סט. ג'ורג'"] = "Kidus Giorgis" # Was "kidus giorgis" (Title case)
mappings["וולייטה דישה"] = "Wolaita Dicha" # Ensure casing

with open(path, "w", encoding="utf-8") as f:
    json.dump(mappings, f, indent=4, ensure_ascii=False)

print("Updated mappings.")
