
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrapers.unibet import UnibetScraper

from scrapers.winner import WinnerScraper

async def analyze_coverage():
    print("Starting Coverage Analysis (Unibet vs Winner)...")
    
    unibet = UnibetScraper(headless=False)
    winner = WinnerScraper(headless=True)
    
    print("Fetching odds from both bookmakers...")
    results = await asyncio.gather(
        unibet.get_odds(),
        winner.get_odds(),
        return_exceptions=True
    )
    
    unibet_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
    winner_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
    
    print("\n" + "="*50)
    print("COMPARATIVE RESULTS")
    print("="*50)
    
    print(f"Total Unibet Matches: {len(unibet_df)}")
    print(f"Total Winner Matches: {len(winner_df)}")
    
    if not unibet_df.empty:
        # Extract league from link
        # Format: .../filter/football/country/league
        def extract_league(url):
            try:
                parts = url.strip('/').split('/')
                return parts[-1]
            except:
                return "unknown"
                
        unibet_df['league'] = unibet_df['link'].apply(extract_league)
        
        print("\nUnibet Coverage by League:")
        print(unibet_df['league'].value_counts())
        
    print("\n" + "="*50)
    
    # Optional: Simple overlap check if both have data
    if not unibet_df.empty and not winner_df.empty:
        from calculations import compare_games
        # Add dummy source columns if needed usually handled in main
        unibet_df['source'] = 'Unibet'
        winner_df['source'] = 'Winner'
        
        # We assume compare_games compares two dfs.
        # But compare_games logic is specific to finding arbs.
        # We just want to find Matches.
        # Let's use a simpler check:
        # Check how many Unibet team names appear in Winner (fuzzy match)
        
        print("\nEstimating Overlap...")
        # (This is a rough estimation)
        pass

if __name__ == "__main__":
    asyncio.run(analyze_coverage())
