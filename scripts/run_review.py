
import asyncio
import sys
import os
import pandas as pd
import json

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.translation_suggester import suggest_translations, save_suggestions

async def run_review():
    print("--- Starting Translation Review Run ---")
    
    # Try loading from logs first (as main.py saves them now)
    winner_path = "logs/winner_matches.csv"
    unibet_path = "logs/unibet_matches.csv"
    
    
    if os.path.exists(winner_path) and os.path.exists(unibet_path):
        print("Loading data from logs/ CSVs...")
        try:
            winner_df = pd.read_csv(winner_path)
            unibet_df = pd.read_csv(unibet_path)
            # Ensure date column is string
            winner_df['date'] = winner_df['date'].astype(str)
            unibet_df['date'] = unibet_df['date'].astype(str)
            
            # LOAD AND APPLY MAPPINGS (Crucial for verifying fixes without re-scraping)
            try:
                with open("data/name_mappings.json", "r", encoding="utf-8") as f:
                    mappings = json.load(f)
                
                print(f"Applying {len(mappings)} mappings to validatation data...")
                # Apply to Winner DF (Team1/Team2 are usually English or Header, Team1_Hebrew is source)
                # We trust 'team1_hebrew' column exists in logs
                if 'team1_hebrew' in winner_df.columns:
                    winner_df['team1'] = winner_df.apply(lambda x: mappings.get(x['team1_hebrew'], x['team1']), axis=1)
                    winner_df['team2'] = winner_df.apply(lambda x: mappings.get(x['team2_hebrew'], x['team2']), axis=1)
            except Exception as e:
                print(f"Warning: Could not apply new mappings: {e}")

        except Exception as e:
            print(f"Error reading logs: {e}")
            return
    else:
        print("Logs not found. Please run main.py first to generate data.")
        return
    
    print(f"Data Loaded: Winner ({len(winner_df)}), Unibet ({len(unibet_df)})")
    
    if winner_df.empty or unibet_df.empty:
        print("One or both datasets are empty. Cannot suggest translations.")
        return

    print("Analyzing for translation suggestions...")
    suggestions = suggest_translations(winner_df, unibet_df)
    
    if suggestions:
        print(f"Found {len(suggestions)} new translation suggestions!")
        save_suggestions(suggestions, filename='reports/translation_suggestions.json')
        
        # Also print preview
        print("\nPreview of suggestions:")
        count = 0
        for heb, eng in suggestions.items():
            print(f"  {heb} -> {eng}")
            count += 1
            if count >= 10:
                print("  ... (see file for more)")
                break
    else:
        print("No new suggestions found. All Winner matches are either matched or completely distinct.")

if __name__ == "__main__":
    asyncio.run(run_review())
