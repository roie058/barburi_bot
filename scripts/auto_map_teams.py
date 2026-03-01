import pandas as pd
import json
import os
from datetime import datetime
import difflib

def similarity(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()

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

def main():
    print("Loading match logs...")
    try:
        winner_df = pd.read_csv("logs/winner_matches.csv")
        unibet_df = pd.read_csv("logs/unibet_matches.csv")
    except Exception as e:
        print(f"Error loading logs: {e}")
        return

    # Normalize Dates
    winner_df['date_obj'] = pd.to_datetime(winner_df['date'], format='%y%m%d', errors='coerce').dt.date
    unibet_df['date_obj'] = pd.to_datetime(unibet_df['date'], errors='coerce').dt.date

    mappings = load_mappings()
    new_mappings_count = 0

    print(f"Analyzing {len(winner_df)} Winner games vs {len(unibet_df)} Unibet games...")

    # Iterate Winner Games
    for _, w_row in winner_df.iterrows():
        w_team1_heb = w_row['team1_hebrew']
        w_team2_heb = w_row['team2_hebrew']
        w_date = w_row['date_obj']

        if pd.isna(w_date): continue

        # Filter Unibet by Date (Exact match or +-1 day)
        # Note: Since we fixed dates, we expect exact or very close matches
        candidates = unibet_df[
            (unibet_df['date_obj'] >= w_date) & 
            (unibet_df['date_obj'] <= w_date) # Strict date match for auto-mapping safe guard
        ]

        if candidates.empty:
            continue

        # Check for Strong Date+Odds+Name correlation?
        # Actually, simpler: Use the Fuzzy Matcher logic but capture the result as a Permanent Mapping
        
        # We need to guess which Unibet game matches this Winner game
        best_match = None
        best_score = 0

        # Current Translation
        w_team1_eng = mappings.get(w_team1_heb, w_row['team1']) # Fallback to existing English
        w_team2_eng = mappings.get(w_team2_heb, w_row['team2'])

        for _, u_row in candidates.iterrows():
            u_team1 = u_row['team1']
            u_team2 = u_row['team2']

            # Compare Team 1
            s1 = similarity(w_team1_eng.lower(), u_team1.lower())
            # Compare Team 2
            s2 = similarity(w_team2_eng.lower(), u_team2.lower())
            
            avg_score = (s1 + s2) / 2
            
            if avg_score > best_score:
                best_score = avg_score
                best_match = u_row

        # Threshold for "This is definitely the same game"
        # Since date is exact, we can be lenient on name (e.g. 0.4) IF we want to discover NEW mappings
        # But for safety, let's look for partial matches (one team matches well)
        
        if best_match is not None and best_score > 0.4: # Low threshold because we want to catch mismatches
            u_team1 = best_match['team1']
            u_team2 = best_match['team2']
            
            # Propose Mappings if not identical
            if w_team1_eng != u_team1:
                # If we don't have a mapping for this Hebrew name, OR the mapping is different
                if w_team1_heb not in mappings or mappings[w_team1_heb] != u_team1:
                    print(f"Suggesting: '{w_team1_heb}' -> '{u_team1}' (Old: {w_team1_eng}) [Score: {best_score:.2f}]")
                    mappings[w_team1_heb] = u_team1
                    new_mappings_count += 1
            
            if w_team2_eng != u_team2:
                if w_team2_heb not in mappings or mappings[w_team2_heb] != u_team2:
                    print(f"Suggesting: '{w_team2_heb}' -> '{u_team2}' (Old: {w_team2_eng}) [Score: {best_score:.2f}]")
                    mappings[w_team2_heb] = u_team2
                    new_mappings_count += 1

    if new_mappings_count > 0:
        save_mappings(mappings)
        print(f"Added/Updated {new_mappings_count} mappings.")
    else:
        print("No new mappings found.")

if __name__ == "__main__":
    main()
