import asyncio
import sys
import os

# Add root directory to path to allow importing 'scrapers'
sys.path.append(os.getcwd())

from scrapers.unibet import UnibetScraper
import pandas as pd

async def verify_recovery():
    print("--- Verifying Unibet Recovery ---")
    scraper = UnibetScraper(headless=False)
    
    # Target Premier League as it had missing games
    print("Scraping Premier League...")
    df = await scraper.get_odds(leagues=["football/england/premier_league"])
    
    print(f"\nTotal Matches Found: {len(df)}")
    
    # Check for specific missing games
    missing_targets = [
        "Everton", "Brentford", "Tottenham", "Sunderland", 
        "Leeds", "Manchester United", "Newcastle", "Crystal Palace"
    ]
    
    found_targets = []
    
    if not df.empty:
        print("\n--- Matches Found ---")
        for index, row in df.iterrows():
            print(f"{row['game']} | {row['date']} | {row.get('raw_header', 'N/A')}")
            
            for t in missing_targets:
                if t in row['game']:
                    found_targets.append(row['game'])

    print("\n--- Verification Results ---")
    if len(df) > 0:
        print("SUCCESS: Matches are being found.")
    else:
        print("FAILURE: Still 0 matches.")

    found_targets = list(set(found_targets))
    print(f"Target Teams Found: {len(found_targets)} / {len(missing_targets)} (Approx)")
    print(found_targets)

if __name__ == "__main__":
    asyncio.run(verify_recovery())
