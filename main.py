import asyncio
import time
import pandas as pd
from scrapers.pinnacle import PinnacleScraper
from scrapers.winner import WinnerScraper

"""""
from calculations import compare_games
from message import bet_notifications
from message_state import should_send_notification, mark_notification_sent

RUN_INTERVAL_SECONDS = 60

# Global cache for last successful runs
LAST_SUCCESSFUL_WINNER = pd.DataFrame()
LAST_SUCCESSFUL_PINNACLE = pd.DataFrame()

async def run_bot():
    """
    Main execution function.
    1. Scrapes Winner and Pinnacle odds.
    2. Compares them to find matches with 'Favorite Flip'.
    3. Prints/Notifications the opportunities.
    """
    print("Starting bot run...")
    
    # Initialize scrapers
    pinnacle = PinnacleScraper(headless=True)
    winner = WinnerScraper(headless=True)
    
    # Run in parallel
    print("Fetching odds...")
    results = await asyncio.gather(
        winner.get_odds(),
        pinnacle.get_odds(),
        return_exceptions=True
    )
    
    winner_df = results[0]
    pinnacle_df = results[1]
    
    # Handle exceptions or empty results
    if isinstance(winner_df, Exception):
        print(f"Winner scraper failed: {winner_df}")
        winner_df = pd.DataFrame()
    if isinstance(pinnacle_df, Exception):
        print(f"Pinnacle scraper failed: {pinnacle_df}")
        pinnacle_df = pd.DataFrame()
        
    print(f"Got {len(winner_df)} Winner matches and {len(pinnacle_df)} Pinnacle matches.")

    # Fallback Logic
    global LAST_SUCCESSFUL_WINNER, LAST_SUCCESSFUL_PINNACLE
    
    if winner_df.empty and not LAST_SUCCESSFUL_WINNER.empty:
        print("Winner scraper returned 0 matches. Using data from last successful run.")
        winner_df = LAST_SUCCESSFUL_WINNER
    elif not winner_df.empty:
        LAST_SUCCESSFUL_WINNER = winner_df
        
    if pinnacle_df.empty and not LAST_SUCCESSFUL_PINNACLE.empty:
        print("Pinnacle scraper returned 0 matches. Using data from last successful run.")
        pinnacle_df = LAST_SUCCESSFUL_PINNACLE
    elif not pinnacle_df.empty:
        LAST_SUCCESSFUL_PINNACLE = pinnacle_df
    
    if not winner_df.empty and not pinnacle_df.empty:
        # Add source column if missing
        if 'source' not in winner_df.columns:
            winner_df['source'] = 'Winner'
        if 'source' not in pinnacle_df.columns:
            pinnacle_df['source'] = 'Pinnacle'
            
        # Compare
        print("Comparing for favorite flips...")
        opportunities, compared_count = compare_games(winner_df, pinnacle_df)
        
        print(f"Compared {compared_count} matching games.")
        if opportunities:
            print(f"FOUND {len(opportunities)} ARBITRAGE OPPORTUNITIES!")
            for opp in opportunities:
                # Check if we already sent this notification
                if not should_send_notification(opp):
                    continue

                print(opp)
                try:
                    bet_notifications(odds_data=opp)
                    mark_notification_sent(opp)
                except Exception as e:
                    print(f"Error sending notification: {e}")
        else:
            print("No opportunities found.")
    else:
        print("Insufficient data for comparison.")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Bot encountered an error: {e}")
            
        print(f"Waiting {RUN_INTERVAL_SECONDS} seconds...")
        time.sleep(RUN_INTERVAL_SECONDS)
