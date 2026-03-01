import json
import os

def fix_mappings():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on investigation
    corrections = {
        "אוניון ברלין": "1. FC Union Berlin", # Winner: Union Berlin -> Unibet: 1. FC Union Berlin
        "פנרבחצ'ה": "Fenerbahçe",          # Winner: Fenerbahce -> Unibet: Fenerbahçe
        "גזישיר גזיינטפ": "Gaziantep FK",  # Winner: Gazishir -> Unibet: Gaziantep FK (or just Gaziantep?) Unibet 'Galatasaray - Gaziantep'
        # Actually in report it said 'Galatasaray - Gaziantep'. So "Gaziantep".
        "גזישיר גזיינטפ": "Gaziantep",
        "ארצו": "Arezzo",                  # Winner: "his country" (Bad Translation) -> Unibet: Arezzo (Padova vs Mantova? Wait. Unibet Game: Padova - Mantova. Winner: Pesaro 1898 - his country???)
        # Wait, Line 163 in CSV: "Pesaro 1898 - his country" (Hebrew: ארצו). "ארצו" means "His Country". It IS "Arezzo".
        # But unmatched game is 'Padova - Mantova'. Winner 138: 'Padua - Mantova 1911'.
        "פאדובה": "Padova",
        "מנטובה 1911": "Mantova",
        "ונציה": "Venezia",  # Already Venezia? Winner: Venezia - Catanzaro 1929. Unibet: Venezia - Catanzaro.
        "קטנזארו 1929": "Catanzaro",
        "סט. פאולי": "St. Pauli", # Winner: Borussia Dortmund - Set. Paulie (Line 116).
        "סט. פאולי": "St. Pauli" # Hebrew to St. Pauli.
    }
    
    count = 0
    for k, v in corrections.items():
        if k in mappings:
            print(f"Updating '{k}': '{mappings[k]}' -> '{v}'")
            mappings[k] = v
            count += 1
        else:
            print(f"Adding '{k}': '{v}'")
            mappings[k] = v
            count += 1
            
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Fixed {count} name mappings.")

if __name__ == "__main__":
    fix_mappings()
