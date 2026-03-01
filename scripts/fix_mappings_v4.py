import json
import os

def fix_mappings_v4():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on Run 5 Report
    corrections = {
        # CRITICAL: Oman League bad translations
        "אל שיב": "Al-Seeb",       # Was "Manchester City" (!!!)
        "סחם": "Saham",            # Was "Chelsea" (!!!)
        "דופר": "Dhofar",          # Was "Duper"
        
        # Belgian Pro League
        "סן ז'ילואז": "Union Saint-Gilloise", # Was "Saint Gilois"
        
        # German/Dutch Characters
        "פרויסן מונסטר": "Preussen Munster", # Keep ASCII, Unibet might need fuzzy or ASCII. 
        # Actually Unibet uses "Preußen Münster". Mapping to that might help if Fuzzy logic expects it.
        # But 'ss' usually matches 'ß'.
        
        # Others
        "ולאנסיין": "Valenciennes", # "Valancen"
        "בורז' פוט 18": "Bourges Foot 18", # "Borg A Bears" ?? (Hebrew: בורז'?)
        "פלורי 91": "FC Fleury 91", # "Florrie"
        "אורליאן": "Orleans",       # "Orleans" (Already likely correct)
        
        # "Champions Crate" -> Hebrew "צ'מפיונס קרייט"? No, likely "CSM Slatina" or similar?
        # Unmatched line 161: "Champions Crate - A.C.S.B"
        # Hebrew source likely: "צ'מפיונס - ..." ??
        # Skip for now.
    }
    
    count = 0
    for k, v in corrections.items():
        if k in mappings:
            print(f"Updating '{k}': '{mappings[k]}' -> '{v}'")
            mappings[k] = v
            count += 1
            
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Fixed {count} name mappings.")

if __name__ == "__main__":
    fix_mappings_v4()
