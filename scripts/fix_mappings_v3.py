import json
import os

def fix_mappings_v3():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on investigation & report
    corrections = {
        # Fix Bad Copy-Paste (Al-Najma duplicates)
        "אל מוחארק": "Al-Muharraq", # Was "Al-Najma"
        "אל בודאייה": "Al-Budaiya", # Was "Al-Najma"
        
        # Fix "Funny Translations" from Report
        "פ.צ. קלן": "1. FC Koln", # "P.C. cologne" -> 1. FC Koln
        "זוולה": "PEC Zwolle",    # "Zola"? Assuming Zola = Zwolle (Hebrew usually זוולה)
        "זולה": "PEC Zwolle",     # Covering typo
        
        # Goztepe variation
        "גוזטפה": "Goztepe",      # Was "Göztepe". Unibet might use "Goztepe" (seen in some inputs).
        # Note: If Unibet uses "Göztepe", "Goztepe" usually fuzzies well (0.9). 
        # But if strict match failed, let's try standardizing.
        
        # Other from report
        "אייאקס מילואים": "Jong Ajax", # "Ajax reserve" -> Jong Ajax (Unibet Standard)
        "פ.ס.וו מילואים": "Jong PSV",  # "PSV Eindhoven reserve" -> Jong PSV
        "אלקמאר מילואים": "Jong AZ",   # "Alkmaar reserve" -> Jong AZ
        "אוטרכט מילואים": "Jong Utrecht", # "Utrecht reserves" -> Jong Utrecht
        
        # "Champions Crate" - ??? 
        # "Chesikzarda Myrkorea" -> Csikszereda Miercurea Ciuc (Romanian)
        "צ'יקסרדה": "Csikszereda",
        
        # "Petrolol Floishti" -> Petrolul Ploiesti
        "פטרולול פלויישט": "Petrolul Ploiesti",
        
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
    fix_mappings_v3()
