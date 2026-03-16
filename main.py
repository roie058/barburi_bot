import asyncio
print("DEBUG: LOADED MODIFIED MAIN.PY")
import time
import pandas as pd
import json
import os
from scrapers.pinnacle import PinnacleScraper
from scrapers.winner import WinnerScraper
from scrapers.unibet import UnibetScraper
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
    pinnacle = PinnacleScraper(headless=True) # Re-enabled for fallback
    winner = WinnerScraper(headless=True)
    unibet = UnibetScraper(headless=False) # MUST remain False to bypass Bot Detection (Kambi) 
    
    # Run in parallel
    # Run Winner first to optimize Unibet
    print("Fetching Winner odds first...")
    try:
        winner_df = await winner.get_odds()
    except Exception as e:
        print(f"Winner scraper failed: {e}")
        winner_df = pd.DataFrame()

    unibet_target_leagues = None # Default to None (All) if winner fails or empty
    
    try:
        if not winner_df.empty and 'league' in winner_df.columns:
            active_leagues = winner_df['league'].unique()
            # Log count only
            with open("debug_main_state.txt", "w", encoding="utf-8") as f:
                  f.write(f"Active Leagues Count: {len(active_leagues)}\n")
            
            print(f"Targeting {len(active_leagues)} active leagues for Unibet mapping.")
            
            # Load Unibet mapping
            mapping_unibet = {}
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                map_path_u = os.path.join(base_dir, "winner_to_unibet_leagues.json")
                if not os.path.exists(map_path_u): map_path_u = "winner_to_unibet_leagues.json"
                
                with open(map_path_u, "r", encoding="utf-8") as f:
                    mapping_unibet = json.load(f)
            except Exception as e:
                print(f"Unibet Mapping file error: {e}")

            unibet_target_leagues = []
            for l in active_leagues:
                if l in mapping_unibet and mapping_unibet[l]:
                    url = mapping_unibet[l]
                    if "/betting/odds/" in url:
                        suffix = url.split("/betting/odds/")[1]
                        unibet_target_leagues.append(suffix)
            
            unibet_target_leagues = list(set(unibet_target_leagues))

            # Load Pinnacle mapping
            mapping_pinnacle = {}
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                map_path_p = os.path.join(base_dir, "winner_to_pinnacle_leagues.json")
                if not os.path.exists(map_path_p): map_path_p = "winner_to_pinnacle_leagues.json"
                
                with open(map_path_p, "r", encoding="utf-8") as f:
                    mapping_pinnacle = json.load(f)
            except Exception as e:
                pass # Expected if it doesn't exist yet

            pinnacle_target_leagues = []
            for l in active_leagues:
                if l in mapping_pinnacle and mapping_pinnacle[l]:
                    pinnacle_target_leagues.append(mapping_pinnacle[l])
            pinnacle_target_leagues = list(set(pinnacle_target_leagues))

            with open("debug_main_state.txt", "a", encoding="utf-8") as f:
                f.write(f"Target Unibet Count: {len(unibet_target_leagues)}\n")
                f.write(f"Target Pinnacle Count: {len(pinnacle_target_leagues)}\n")

            print(f"Optimization: Mapped to {len(unibet_target_leagues)} Unibet leagues and {len(pinnacle_target_leagues)} Pinnacle leagues.")
    except Exception as e:
        print(f"Optimization crash: {e}")

    
    print("Fetching Unibet and Pinnacle odds...")
    results = await asyncio.gather(
        pinnacle.get_odds(leagues=pinnacle_target_leagues),
        unibet.get_odds(leagues=unibet_target_leagues),
        return_exceptions=True
    )
    
    pinnacle_df = results[0]
    unibet_df = results[1]
    
    # Handle exceptions
    if isinstance(pinnacle_df, Exception):
        print(f"Pinnacle scraper failed: {pinnacle_df}")
        pinnacle_df = pd.DataFrame()
    if isinstance(unibet_df, Exception):
        print(f"Unibet scraper failed: {unibet_df}")
        unibet_df = pd.DataFrame()
        
    print(f"Got {len(winner_df)} Winner, {len(unibet_df)} Unibet, {len(pinnacle_df)} Pinnacle matches.")
    
    # Check/Create logs dir
    if not os.path.exists("logs"): os.makedirs("logs")

    # Save CSVs for review script
    if not winner_df.empty:
        winner_df.to_csv("logs/winner_matches.csv", index=False)
    if not unibet_df.empty:
        unibet_df.to_csv("logs/unibet_matches.csv", index=False)

    # Fallback Logic for Unibet (Replaces Pinnacle logic for now)
    global LAST_SUCCESSFUL_WINNER, LAST_SUCCESSFUL_PINNACLE
    # Note: Using LAST_SUCCESSFUL_PINNACLE variable to store Unibet fallback to minimize global changes, 
    # or should I add LAST_SUCCESSFUL_UNIBET? Better adds new one but let's reuse/add properly.
    # Actually, let's keep it simple.
    
    if winner_df.empty and not LAST_SUCCESSFUL_WINNER.empty:
        print("Winner scraper returned 0 matches. Using data from last successful run.")
        winner_df = LAST_SUCCESSFUL_WINNER
    elif not winner_df.empty:
        LAST_SUCCESSFUL_WINNER = winner_df
        
    # Skip Pinnacle fallback logic as it's disabled.
    # Add Unibet fallback if needed (optional, skipping for now)
    
    # Logic: If we have Winner and Unibet, compare them.
    # Logic: If we have Winner and Unibet, compare them.
    # Fallback Logic: Winner vs Unibet (Primary) -> Unmatched vs Pinnacle (Secondary)
    
    all_opportunities = []
    
    if not winner_df.empty:
        # Add source column if missing
        if 'source' not in winner_df.columns: winner_df['source'] = 'Winner'
        if not unibet_df.empty and 'source' not in unibet_df.columns: unibet_df['source'] = 'Unibet'
        if not pinnacle_df.empty and 'source' not in pinnacle_df.columns: pinnacle_df['source'] = 'Pinnacle'
            
        # 1. Compare Winner vs Unibet
        unmatched_winner_df = winner_df # Default if unibet empty
        
        if not unibet_df.empty:
            print("Comparing Winner vs Unibet (Primary) for favorite flips...")
            unibet_opps, unibet_matched_count, unibet_matched_indices = compare_games(winner_df, unibet_df, remote_name="Unibet")
            
            print(f"Compared {unibet_matched_count} matching games with Unibet.")
            all_opportunities.extend(unibet_opps)
            
            # Filter unmatched for next step
            # Use dataframe index loc matching
            matched_indices_set = set(unibet_matched_indices)
            unmatched_winner_df = winner_df.iloc[[i for i in range(len(winner_df)) if i not in matched_indices_set]]
            
        # 2. Compare Unmatched Winner vs Pinnacle
        pinnacle_matched_indices = []
        if not pinnacle_df.empty and not unmatched_winner_df.empty:
            print(f"Comparing {len(unmatched_winner_df)} Unmatched Winner games vs Pinnacle (Secondary)...")
            pinnacle_opps, pinnacle_matched_count, pinnacle_matched_indices = compare_games(unmatched_winner_df, pinnacle_df, remote_name="Pinnacle")
            
            print(f"Compared {pinnacle_matched_count} matching games with Pinnacle.")
            all_opportunities.extend(pinnacle_opps)
            
        # Generate Run Report
        try:
            with open("reports/last_run_report.md", "w", encoding="utf-8") as f:
                f.write(f"# Bot Run Report - {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Statistics\n")
                f.write(f"- Total Winner Games: {len(winner_df)}\n")
                f.write(f"- Matched with Unibet (Primary): {len(unibet_matched_indices) if not unibet_df.empty else 0}\n")
                f.write(f"- Matched with Pinnacle (Secondary): {len(pinnacle_matched_indices)}\n")
                f.write(f"- Total Unmatched: {len(winner_df) - (len(unibet_matched_indices) if not unibet_df.empty else 0) - len(pinnacle_matched_indices)}\n\n")
                
                f.write("## Pinnacle Fallback Matches (Missing/Unmatched in Unibet)\n")
                if pinnacle_matched_indices:
                    # These are indices relative to unmatched_winner_df, which is a slice.
                    # We need to get the actual game rows.
                    # unmatched_winner_df.iloc[i] works if we iterate the matched list.
                    
                    matches = unmatched_winner_df.iloc[pinnacle_matched_indices]
                    for _, row in matches.iterrows():
                        f.write(f"- {row['game']} ({row['date']})\n")
                else:
                    f.write("No fallback matches found.\n")
                    
                f.write("\n## Completely Unmatched Games\n")
                # Identify completely unmatched
                # It's unmatched_winner_df MINUS pinnacle_matched_indices
                pinnacle_matched_set = set(pinnacle_matched_indices)
                completely_unmatched = unmatched_winner_df.iloc[[i for i in range(len(unmatched_winner_df)) if i not in pinnacle_matched_set]]
                
                for _, row in completely_unmatched.iterrows():
                    f.write(f"- {row['game']} ({row['date']})\n")
                    
            print("Report saved to reports/last_run_report.md")
        except Exception as e:
            print(f"Error generating report: {e}")

        # Report Results
        if all_opportunities:
            print(f"FOUND {len(all_opportunities)} ARBITRAGE OPPORTUNITIES!")
            for opp in all_opportunities:
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
        print("Insufficient data for comparison (Needs Winner Data).")

if __name__ == "__main__":
    #while True:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
        # break
    except Exception as e:
        print(f"Bot encountered an error: {e}")
            
    # print(f"Waiting {RUN_INTERVAL_SECONDS} seconds...")
    # time.sleep(RUN_INTERVAL_SECONDS)
