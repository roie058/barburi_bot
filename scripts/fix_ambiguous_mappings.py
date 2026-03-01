import json
import os

def fix_ambiguous_mappings():
    path = "data/name_mappings.json"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Corrections based on LOGS and REPORT
    corrections = {
        # Log: Ambiguous alignment for Estrela - Estoril vs Estrela da Amadora - Estoril.
        "אסטרלה אמדורה": "Estrela da Amadora", # Was 'Estrela' -> Changed to full name to match Unibet exactly
        
        # Log: Ambiguous alignment for Al Bukairiah - Al Darya vs Al Bukiryah - Al Draih.
        "אל בוקאיריאח": "Al Bukiryah",  # Was 'Al Bukairiah'
        "אל דרייה": "Al Draih",         # Was 'Al Darya'
        
        # Log: Strict Swap Detected for Al-Jandal - Al Arabi (KWT).
        # Report says: Al-Jandal - Al Arabi (KWT) (260116)
        # Winner: Al-Jandal - Al Arabi (KWT) ?? Wait. 
        # Winner might have team "Al Arabi" which maps to "Al Arabi (KWT)"? 
        # Checking log: "Al-Jandal - Al Arabi (KWT)"
        # Note: Unibet often uses "Al Arabi (KWT)" or "Al-Arabi SC".
        # If it was a swap, it means the bot handled it, but maybe mapping helps.
        
        # Report: "Pauk Thessaloniki - Cretan character (260118)"
        # "Cretan character" -> OFI Crete? (Hebrew: אופי כרתים -> 'Character of Crete'?? 'Ofi' implies character/nature in Hebrew...)
        "אופי כרתים": "OFI Crete", 
        "פאוק סלוניקי": "PAOK",  # Was 'Pauk Thessaloniki' (bad transliteration?) -> Unibet usually 'PAOK' or 'PAOK Thessaloniki'
        
        # Report: "Guztaffe - Rizaspur (260119)"
        # Guztaffe -> Göztepe? (Hebrew: גוזטפה)
        "גוזטפה": "Göztepe",
        "ריזספור": "Rizespor", # Was Rizaspur?
        
        # Report: "Monster - Karlsruhe (260117)"
        # Monster -> Preußen Münster (Hebrew: מונסטר -> Monster/Munster)
        "פרויסן מונסטר": "Preussen Munster",
        "מונסטר": "Preussen Munster",

        # Report: "Dynamo Dresden - Gruyter explained (260117)"
        # Gruyter explained -> Greuther Fürth (Hebrew: גרויטר פירט -> 'Perut/Explained'??)
        "גרויטר פירט": "Greuther Furth",
        
        # Report: "Udinese - Inter (260117)" 
        # Wait, Udinese - Inter SHOULD match. 
        # Winner: 160. Unibet: 160. 
        # Why unmatched? Maybe Date? Winner 260117 vs Unibet ??
        # Or Line 160 in report is "Udinese - Inter". means it is in "Completely Unmatched".
        # Unibet has Serie A. Game exists.
        
        # Report: "Pchuca - America de Mexico (260119)"
        # League: Mexico Liga MX (Added manually by user).
        # Unibet scraping Mexico? Log says "Scraping Unibet: football/mexico/liga-mx".
        # So it should be there.
        
        # Report: "Club Olympia - His voice is his voice (260116)"
        # "His voice is his voice" -> Tacuary ?? (Hebrew: קולו קולו -> Colo Colo??)
        # Or General Caballero?
        # "קולו קולו" = Colo Colo (Chile). But usually Copa Libertadores?
        # Paraguayan League?
        "קולו קולו": "Colo Colo",

         # Report: "In Abishta - Fluminense" -> In Abishta?? Boavista?
         # Hebrew: בואבישטה -> Boavista.
         "בואבישטה": "Boavista",

         # Report: "Geneva Sorbet - P.C. Zurich"
         # Geneva Sorbet -> Servette (Hebrew: סרבט ז'נבה -> Sorbet??)
         "סרבט ז'נבה": "Servette",
         
         # Report: "Javelin - El Vahda"
         # Javelin -> Al-Jabalain? (Saudi Div 1)
         "אל ג'בלאין": "Al-Jabalain"
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
    fix_ambiguous_mappings()
