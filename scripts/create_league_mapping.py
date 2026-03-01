import json
import difflib

# Load Winner leagues
winner_leagues = []
try:
    with open("logs/extracted_winner_leagues.txt", "r", encoding="utf-8") as f:
        winner_leagues = [l.strip() for l in f.readlines() if l.strip()]
except FileNotFoundError:
    print("Winner leagues file not found.")
    exit()

# Load Unibet leagues
unibet_leagues = []
try:
    with open("data/unibet_leagues.json", "r", encoding="utf-8") as f:
        unibet_leagues = json.load(f)
except FileNotFoundError:
    print("Unibet leagues file not found.")
    exit()

# Simple translation/mapping dictionary (Hardcoded common ones)
# This serves as a base.
manual_mapping = {
    "NBA": "basketball/nba",
    "אוסטרלית ראשונה": "football/australia/a-league",
    "אוסטרלית ראשונה, נשים": "football/australia/a-league-women",
    "איטלקית ראשונה": "football/italy/serie-a",
    "איטלקית שניה": "football/italy/serie-b",
    "איטלקית שלישית, בית א'": "football/italy/serie-c-group-a", # Approximate
    "איטלקית שלישית, בית ב'": "football/italy/serie-c-group-b", # Approximate
    "איטלקית שלישית, בית ג'": "football/italy/serie-c-group-c", # Approximate
    "אנגלית מחוזית, דרום": "football/england/national-league-south",
    "גביע אפריקה לאומות": "football/international/africa-cup-of-nations",
    "גרמנית ראשונה": "football/germany/bundesliga",
    "ידידות בינלאומי": "football/international/friendlies", # Approximate
    "יורוליג": "basketball/euroleague",
    "ליגת Winner": "football/israel/ligat-ha-al",
    "ליגת Winner סל": "basketball/israel/super-league",
    "ליגה לאומית": "football/israel/liga-leumit",
    "ליגת האלופות": "football/uefa-club/uefa-champions-league",
    "סופר קאפ ספרדי": "football/spain/super-cup",
    "סינית ראשונה": "football/china/super-league",
    "סעודית ראשונה": "football/saudi-arabia/saudi-prof-league",
    "סעודית שניה": "football/saudi-arabia/division-1",
    "ספרדית ראשונה": "football/spain/la-liga",
    "ספרדית שניה": "football/spain/segunda-division",
    "סקוטית ראשונה": "football/scotland/premiership",
    "פוטבול אמריקאי": "american-football/nfl",
    "פורטוגלית ראשונה": "football/portugal/primeira-liga",
    "פורטוגלית שניה": "football/portugal/liga-portugal-2",
    "פרמייר ליג": "football/england/premier-league",
    "צ'מפיונשיפ": "football/england/championship",
    "צרפתית ראשונה": "football/france/ligue-1",
    "צרפתית שניה": "football/france/ligue-2",
    "קטארית ראשונה": "football/qatar/stars-league", # Verify if present
    "קפריסאית ראשונה": "football/cyprus/1st-division",
    "קרואטית ראשונה": "football/croatia/hnl",
    "טורקית ראשונה": "football/turkey/super-lig",
    "סרבית ראשונה": "football/serbia/superliga",
    "אתיופית ראשונה": "football/ethiopia/premier-league",
    "אלג'יראית ראשונה": "football/algeria/ligue-1", # Verify
    "אינדונזית ראשונה": "football/indonesia/liga-1",
    "איסלנדית ראשונה": "football/iceland/urvalsdeild", # Verify
}

final_mapping = {}

# Process each Winner league
for w_league in winner_leagues:
    # 1. Check manual mapping first
    if w_league in manual_mapping:
         # Try to find specific Unibet match
         target_suffix = manual_mapping[w_league]
         matched = None
         for u_link in unibet_leagues:
             if u_link.endswith(target_suffix):
                 matched = u_link
                 break
         
         if matched:
             final_mapping[w_league] = matched
         else:
             # Just use the manual suffix as best effort or try to find close match
             final_mapping[w_league] = f"https://www.unibet.co.uk/betting/odds/{target_suffix}"
    
    else:
        # 2. Try simple heuristic? (Not reliable for Hebrew -> English without translation)
        # Leave null/empty for user to fill
        final_mapping[w_league] = None

# Save to JSON
with open("winner_to_unibet_leagues.json", "w", encoding="utf-8") as f:
    json.dump(final_mapping, f, indent=4, ensure_ascii=False)

print(f"Created mapping for {len(final_mapping)} leagues.")
print("Saved to winner_to_unibet_leagues.json")
