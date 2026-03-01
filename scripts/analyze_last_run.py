import pandas as pd
import json
import os
import sys

# Add parent dir to path so we can import 'calculations'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculations import compare_games, Game

def investigate():
    print("INVESTIGATING DATA GAPS...")
    
    # 1. Load Data
    try:
        winner_df = pd.read_csv("logs/winner_matches.csv")
        unibet_df = pd.read_csv("logs/unibet_matches.csv")
        with open("winner_to_unibet_leagues.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    with open("investigation_report.txt", "w", encoding="utf-8") as f:
        f.write("INVESTIGATING DATA GAPS...\n")

        # 2. Analyze Unmapped Leagues
        if 'league' in winner_df.columns:
            active_leagues = winner_df['league'].unique()
            unmapped = [l for l in active_leagues if l not in mapping or not mapping[l]]
            
            f.write(f"\n--- UNMAPPED LEAGUES ({len(unmapped)}) ---\n")
            for l in unmapped:
                 f.write(f"MISSING: {l}\n")

        # 3. Analyze Comparison Discrepancy (CORRECTED LOGIC)
        f.write(f"\n--- MATCHING ANALYSIS ---\n")
        f.write(f"Winner: {len(winner_df)}, Unibet: {len(unibet_df)}\n")
        
        if not winner_df.empty and not unibet_df.empty:
            # We need to know which UNIBET games were matched.
            # compare_games only returns Winner indices.
            # So we reproduce the matching collection here using the Game objects.
            
            winner_games = [Game(row.to_dict()) for index, row in winner_df.iterrows()]
            remote_games = [Game(row.to_dict()) for index, row in unibet_df.iterrows()]
            
            # Index Remote games by date
            r_by_date = {}
            # Map object back to original index
            game_to_index = {} 
            for idx, g in enumerate(remote_games):
                if g.date not in r_by_date: r_by_date[g.date] = []
                r_by_date[g.date].append(g)
                game_to_index[id(g)] = idx
            
            matched_remote_indices = set()
            matches_found_count = 0
            
            from datetime import datetime, timedelta
            
            for w_game in winner_games:
                # Date Logic
                target_dates = [w_game.date]
                try:
                    w_dt = datetime.strptime(w_game.date, "%Y-%m-%d")
                    target_dates.append((w_dt - timedelta(days=1)).strftime("%Y-%m-%d"))
                    target_dates.append((w_dt + timedelta(days=1)).strftime("%Y-%m-%d"))
                except:
                    pass
                
                potential_remote = []
                for d in target_dates:
                    potential_remote.extend(r_by_date.get(d, []))
                    
                if not potential_remote: continue
                
                best_match = None
                w_key = w_game.get_key()
                
                # Exact Match
                for r_game in potential_remote:
                    if w_key == r_game.get_key():
                        best_match = r_game
                        break
                        
                # Fuzzy Match (Simple check)
                if not best_match:
                     # (Skip complex fuzzy logic for this check - assuming exact match primarily)
                     pass
                
                if best_match:
                    matches_found_count += 1
                    matched_remote_indices.add(game_to_index[id(best_match)])

            f.write(f"Matches Found (Strict/Key): {matches_found_count}\n")
            
            unmatched_unibet_indices = [i for i in range(len(unibet_df)) if i not in matched_remote_indices]
            f.write(f"True Unmatched Unibet Games: {len(unmatched_unibet_indices)}\n")
            
            unmatched_unibet = unibet_df.iloc[unmatched_unibet_indices]
            
            f.write("\n--- TRUE UNMATCHED UNIBET GAMES ---\n")
            for idx, row in unmatched_unibet.iterrows():
                f.write(f"Unibet Game: '{row['game']}' ({row['date']})\n")

    print("Investigation complete. Check investigation_report.txt")

if __name__ == "__main__":
    investigate()
