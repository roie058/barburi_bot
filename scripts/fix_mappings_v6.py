import json
import os

def fix_mappings_v6():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on Run 6 Report & Grep Failure
    corrections = {
        # Missing Major Teams (Winner Key -> Unibet Value)
        "אודינזה": "Udinese",
        "אינטר": "Inter",
        "גוזטפה": "Goztepe",
        "אתלטיקו מדריד": "Atlético Madrid", # Ensure accent
        "אלאבס": "Deportivo Alavés",      # Ensure accent
        
        # Bad Translations from Report
        "אל נחדה": "Al-Nahda",         # Was "El Nahda"
        "אל מוֹקאוולוּן": "El Mokawloon", # Was "to Mokavlon" (Bad Google Translate)
        "אל סאד": "Al-Sadd",           # Was "Al Sadd" (Unibet often uses Dash)
        
        # Others from Unmatched List
        "פורטונה סיטארד": "Fortuna Sittard",
        "איינדהובן": "FC Eindhoven",   # Usually FC Eindhoven in Eerste Divisie
        "פ.ס.וו איינדהובן": "PSV",     # Eredivisie
        
        # "Smiley" -> "Oman"? (Report line 208)
        # "סמאילי" -> "Samail" (Omani Club)
        "סמאילי": "Samail",
        
        # "Sur - organs" (Report line 206)
        # "organs" -> ??? Hebrew: "איברים"? No, "Sur" vs "Ibri"? 
        # "עברי" -> "Ibri"
        "עברי": "Ibri",
        
        # "Kiro - tarflin" (Report line 213)
        # "Kiro" -> "Cairo"? "Kairouan"? 
        # "tarflin" -> ???
        # "י.ס. קירואן" -> "JS Kairouan"
        "י.ס. קירואן": "JS Kairouan",
        
        # "Saccon United" -> "Sekhukhune United" (South Africa)
        # Hebrew: "סוקון יונייטד" or similar?
        "סקוקון יונייטד": "Sekhukhune United",
    }
    
    count = 0
    for k, v in corrections.items():
        print(f"Updating '{k}': '{v}'")
        mappings[k] = v
        count += 1
            
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Fixed {count} name mappings.")

if __name__ == "__main__":
    fix_mappings_v6()
