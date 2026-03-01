import json
import pandas as pd
import difflib
import os

def standardize():
    print("STARTING STANDARDIZATION...")
    
    # 1. Load Mappings
    map_path = "data/name_mappings.json"
    with open(map_path, "r", encoding="utf-8") as f:
        mappings = json.load(f)
        
    # 2. Load Unibet Matches (Reference Gold Standard)
    uni_path = "logs/unibet_matches.csv"
    if not os.path.exists(uni_path):
        print("Unibet logs not found. Cannot standardize.")
        return
        
    try:
        uni_df = pd.read_csv(uni_path)
    except:
        print("Error reading unibet csv")
        return
        
    # Extract unique Team Names from Unibet (Team1 and Team2)
    uni_teams = set(uni_df['team1'].dropna().unique()) | set(uni_df['team2'].dropna().unique())
    
    # Clean Reference Set for matching
    # Map "Clean Name" -> "Official Name"
    # e.g. "manchester city" -> "Manchester City"
    ref_map = {}
    for t in uni_teams:
        clean = t.lower().replace("fc", "").replace("cf", "").strip()
        ref_map[clean] = t
        
    print(f"Loaded {len(uni_teams)} unique Unibet teams as reference.")
    
    updates = 0
    
    for heb, current_val in mappings.items():
        # Clean the current value
        curr_clean = current_val.lower().replace("fc", "").replace("cf", "").strip()
        
        # 1. Exact Match Check (Case insensitive)
        found = False
        for clean_ref, official in ref_map.items():
            if curr_clean == clean_ref:
                if current_val != official:
                    print(f"Snap (Exact): '{current_val}' -> '{official}'")
                    mappings[heb] = official
                    updates += 1
                found = True
                break
        
        if found: continue
            
        # 2. Fuzzy Snap
        # If we have "Man City" and Unibet has "Manchester City", snap it.
        # Threshold: 0.85
        best_ratio = 0
        best_match = None
        
        for clean_ref, official in ref_map.items():
            r = difflib.SequenceMatcher(None, curr_clean, clean_ref).ratio()
            if r > best_ratio:
                best_ratio = r
                best_match = official
                
        if best_ratio > 0.90: # Very Strict snapping
             if current_val != best_match:
                print(f"Snap (Fuzzy {best_ratio:.2f}): '{current_val}' -> '{best_match}'")
                mappings[heb] = best_match
                updates += 1
    
    # Save
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=4)
        
    print(f"Standardized {updates} mappings.")

if __name__ == "__main__":
    standardize()
