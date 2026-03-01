import pandas as pd
import json
import os
import difflib

def load_mappings():
    path = "data/name_mappings.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_mappings(mappings):
    with open("data/name_mappings.json", "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=4, ensure_ascii=False)
    print("Saved mappings to data/name_mappings.json")

def _clean_team_name(name):
    name = str(name).lower()
    suffixes = ["town", "city", "united", "rovers", "athletic", "fc", "afc", " wanderers", " county", " hotspur", " albion", " borough", " sporting"]
    for s in suffixes:
        name = name.replace(s, "")
    if "congo" in name: name = "congo dr"
    return name.strip()

def main():
    print("Loading logs...")
    try:
        winner_df = pd.read_csv("logs/winner_matches.csv")
        unibet_df = pd.read_csv("logs/unibet_matches.csv")
    except Exception as e:
        print(f"Error: {e}")
        return

    mappings = load_mappings()
    updates = 0
    
    print(f"Scanning {len(winner_df)} Winner games vs {len(unibet_df)} Unibet games for Perfect Mappings...")

    # Iterate matching logic
    for _, w_row in winner_df.iterrows():
        w_heb1 = w_row['team1_hebrew']
        w_heb2 = w_row['team2_hebrew']
        
        # Current English (or fallback)
        w_eng1 = mappings.get(w_heb1, w_row['team1'])
        w_eng2 = mappings.get(w_heb2, w_row['team2'])
        
        w1_clean = _clean_team_name(w_eng1)
        w2_clean = _clean_team_name(w_eng2)
        
        best_score = 0
        best_match = None
        
        # Global Search (O(N*M))
        for _, u_row in unibet_df.iterrows():
            u_eng1 = u_row['team1']
            u_eng2 = u_row['team2']
            
            p1_clean = _clean_team_name(u_eng1)
            p2_clean = _clean_team_name(u_eng2)
            
            # Straight
            s1 = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
            s2 = difflib.SequenceMatcher(None, w2_clean, p2_clean).ratio()
            score_straight = (s1 + s2) / 2
            
            # Swapped
            s3 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
            s4 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
            score_swapped = (s3 + s4) / 2
            
            g_score = max(score_straight, score_swapped)
            
            if g_score > best_score:
                best_score = g_score
                best_match = u_row
        
        # Threshold: 0.80 (Same as calculations.py)
        if best_match is not None and best_score > 0.80:
            u_team1 = best_match['team1']
            u_team2 = best_match['team2']
            
            # Determine alignment
            # Check straight vs swapped again for the winner
            p1_c = _clean_team_name(u_team1)
            p2_c = _clean_team_name(u_team2)
            
            s_straight = (difflib.SequenceMatcher(None, w1_clean, p1_c).ratio() + difflib.SequenceMatcher(None, w2_clean, p2_c).ratio())
            s_swapped = (difflib.SequenceMatcher(None, w1_clean, p2_c).ratio() + difflib.SequenceMatcher(None, w2_clean, p1_c).ratio())
            
            final_u1 = u_team1
            final_u2 = u_team2
            if s_swapped > s_straight:
                final_u1 = u_team2
                final_u2 = u_team1
                
            # Update Mappings Only if different
            if w_eng1 != final_u1:
                # If Heb not in mappings, OR mapping matches old English but not Unibet
                # Just FORCE update
                if mappings.get(w_heb1) != final_u1:
                    print(f"Updating: '{w_heb1}' -> '{final_u1}' (Was: '{w_eng1}') [Score: {best_score:.2f}]")
                    mappings[w_heb1] = final_u1
                    updates += 1
            
            if w_eng2 != final_u2:
                if mappings.get(w_heb2) != final_u2:
                    print(f"Updating: '{w_heb2}' -> '{final_u2}' (Was: '{w_eng2}') [Score: {best_score:.2f}]")
                    mappings[w_heb2] = final_u2
                    updates += 1

    if updates > 0:
        save_mappings(mappings)
        print(f"Enforced {updates} perfect mappings.")
    else:
        print("Mappings are already perfect.")

if __name__ == "__main__":
    main()
