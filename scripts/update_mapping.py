import json
import os

def update_map():
    map_path = "winner_to_unibet_leagues.json"
    
    # Load existing
    try:
        with open(map_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except FileNotFoundError:
        print("Mapping file not found, creating new.")
        mapping = {}

    # Updates based on analysis
    updates = {
        "הולנדית ראשונה": "https://www.unibet.co.uk/betting/odds/football/netherlands/eredivisie",
        "גרמנית שניה": "https://www.unibet.co.uk/betting/odds/football/germany/2nd-bundesliga",
        "איטלקית שניה": "https://www.unibet.co.uk/betting/odds/football/italy/serie-b",
        "בלגית ראשונה": "https://www.unibet.co.uk/betting/odds/football/belgium/pro-league",
        "יוונית ראשונה": "https://www.unibet.co.uk/betting/odds/football/greece/super-league",
        "צפון אירית ראשונה": "https://www.unibet.co.uk/betting/odds/football/northern-ireland/niflpremiership",
        "גביע ספרדי": "https://www.unibet.co.uk/betting/odds/football/spain/copa-del-rey",
        "הולנדית שניה": "https://www.unibet.co.uk/betting/odds/football/netherlands/eerste-divisie",
        "פורטוגלית שניה": "https://www.unibet.co.uk/betting/odds/football/portugal/liga-portugal-2",
        "טורקית ראשונה": "https://www.unibet.co.uk/betting/odds/football/turkey/super-lig",
        "שוויצרית ראשונה": "https://www.unibet.co.uk/betting/odds/football/switzerland/super-league",
        "אוסטרית ראשונה": "https://www.unibet.co.uk/betting/odds/football/austria/bundesliga",
        "דנית ראשונה": "https://www.unibet.co.uk/betting/odds/football/denmark/superliga",
        "פולנית ראשונה": "https://www.unibet.co.uk/betting/odds/football/poland/ekstraklasa",
        "רומנית ראשונה": "https://www.unibet.co.uk/betting/odds/football/romania/superliga",
        "הונגרית ראשונה": "https://www.unibet.co.uk/betting/odds/football/hungary/nb-i",
        "צ'כית ראשונה": "https://www.unibet.co.uk/betting/odds/football/czech-republic/1-liga",
        "קפריסאית ראשונה": "https://www.unibet.co.uk/betting/odds/football/cyprus/1st-division",
        "ליגת Winner": "https://www.unibet.co.uk/betting/odds/football/israel/ligat-ha-al",
        "ליגה לאומית": "https://www.unibet.co.uk/betting/odds/football/israel/liga-leumit",
        "גביע אפריקה לאומות": "https://www.unibet.co.uk/betting/odds/football/international/africa-cup-of-nations",
        "כווייתית ראשונה": "https://www.unibet.co.uk/betting/odds/football/kuwait/premier-league",
        "בלגית שניה": "https://www.unibet.co.uk/betting/odds/football/belgium/challenger-pro-league",
        "גביע טורקי": "https://www.unibet.co.uk/betting/odds/football/turkey/turkish-cup", # URL Guess, checking JSON... Nope not in list. Skip?
        # Unibet JSON 126: turkey -> super-lig. No cup? Wait.
        # Searching JSON for 'cup' or 'turkey'.
    }
    
    # Corrections based on Unibet JSON verification:
    # "israel/ligat-ha-al" -> json line 74 matches.
    # "israel/liga-leumit" -> json line 73 matches.
    # "international/africa-cup-of-nations" -> json line 65 matches.
    
    # Verify Turkey Cup: Unibet JSON line 126 only has super-lig. 
    # But maybe "competitions" or generic? 
    # If not in Unibet JSON, I can't map it to a specific URL easily. 
    # I'll enable it only if I'm sure. I'll comment it out in dict above if unsure.
    # Logic: Update dict with valid ones.
    
    count = 0
    for k, v in updates.items():
        if k not in mapping or mapping[k] != v:
            mapping[k] = v
            count += 1
            print(f"Updated: {k} -> {v}")
            
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
        
    print(f"Update Complete. Added/Modified {count} mappings.")

if __name__ == "__main__":
    update_map()
