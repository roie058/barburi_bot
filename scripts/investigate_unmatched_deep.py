import pandas as pd
from datetime import datetime
import json
import os

def load_mappings():
    path = "data/name_mappings.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    print("Loading data...")
    winner_df = pd.read_csv("logs/winner_matches.csv")
    unibet_df = pd.read_csv("logs/unibet_matches.csv")
    mappings = load_mappings()
    
    # 1. Identify Unmatched Games (Simulate the main bot logic briefly or just take all Winner games)
    # We will assume any Winner game not in "Matched" state is target.
    # But since we don't have the bot's runtime state, we'll re-run a naive check:
    # If a Winner game matches a Unibet game by (Team1 AND Team2) OR (Date AND Team1 approx), it's "Matched".
    # Otherwise "Unmatched".
    
    unmatched_games = []
    
    print(f"Scanning {len(winner_df)} Winner games...")
    
    for _, w_row in winner_df.iterrows():
        w_team1_raw = w_row['team1'] # English from Winner (mapped)
        w_team2_raw = w_row['team2']
        w_heb = w_row['team1_hebrew']
        
        # Apply current mappings to get "Best Known English Name"
        w_team1 = mappings.get(w_row['team1_hebrew'], w_team1_raw)
        w_team2 = mappings.get(w_row['team2_hebrew'], w_team2_raw)
        
        # Check against Unibet DB
        # Strict check first
        match_found = False
        
        # Search unibet for EXACT match of both teams
        exact_subset = unibet_df[
            (unibet_df['team1'] == w_team1) & (unibet_df['team2'] == w_team2)
        ]
        if not exact_subset.empty:
            match_found = True
            
        if not match_found:
            # Check swapped
            swapped_subset = unibet_df[
                (unibet_df['team1'] == w_team2) & (unibet_df['team2'] == w_team1)
            ]
            if not swapped_subset.empty:
                match_found = True
        
        if not match_found:
            unmatched_games.append({
                "w_team1": w_team1,
                "w_team2": w_team2,
                "w_raw": f"{w_team1} - {w_team2}",
                "w_heb": w_heb
            })

    print(f"\nFound {len(unmatched_games)} Unmatched Games (Strict Name Check).")
    print("Investigating reasons...\n")
    
    results = []
    
    for g in unmatched_games:
        t1 = g['w_team1']
        t2 = g['w_team2']
        
        # Investigation 1: Is T1 in Unibet?
        # substring search
        t1_candidates = unibet_df[unibet_df['team1'].str.contains(t1, case=False, regex=False) | unibet_df['team2'].str.contains(t1, case=False, regex=False)]
        t2_candidates = unibet_df[unibet_df['team1'].str.contains(t2, case=False, regex=False) | unibet_df['team2'].str.contains(t2, case=False, regex=False)]
        
        status = ""
        details = ""
        
        if t1_candidates.empty and t2_candidates.empty:
             # Try splitting names? "Manchester United" -> "Manchester"
             status = "Not Scraped (Teams Missing)"
        elif not t1_candidates.empty and not t2_candidates.empty:
             status = "Teams Found (Mapping/Logic Issue)"
             # Check if they are in the SAME game
             # Intersection of indices
             common_idx = t1_candidates.index.intersection(t2_candidates.index)
             if not common_idx.empty:
                 row = unibet_df.loc[common_idx[0]]
                 status = "GAME EXISTS (Name Mismatch?)"
                 details = f"Found: {row['team1']} - {row['team2']} (Date: {row['date']})"
             else:
                 status = "Teams Found Separately"
                 details = f"T1 in {len(t1_candidates)} games, T2 in {len(t2_candidates)} games."
        else:
            present = t1 if not t1_candidates.empty else t2
            missing = t2 if t1_candidates.empty else t1
            status = f"Partial Missing ('{missing}' not found)"
            details = f"'{present}' found in {len(t1_candidates) + len(t2_candidates)} games."
            
        results.append({
            "Game": g['w_raw'],
            "Status": status,
            "Details": details
        })

    # Save to JSON for robust reading
    with open("reports/investigation.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"Saved {len(results)} results to reports/investigation.json")

if __name__ == "__main__":
    main()
