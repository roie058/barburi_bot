import sqlite3
import pandas as pd
import asyncio
import os
import time
from datetime import datetime

from scrapers.winner import WinnerScraper

DB_PATH = "data/tracker.sqlite"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Store latest odds
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            game TEXT,
            date TEXT,
            team1 TEXT,
            team2 TEXT,
            team1_hebrew TEXT,
            team2_hebrew TEXT,
            num_1 REAL,
            num_X REAL,
            num_2 REAL,
            link TEXT,
            league TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Store history of changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS odds_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            old_1 REAL,
            old_X REAL,
            old_2 REAL,
            new_1 REAL,
            new_X REAL,
            new_2 REAL,
            change_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Track execution runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_stats (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_matches INTEGER,
            new_matches INTEGER,
            changed_matches INTEGER,
            major_changes INTEGER,
            errors INTEGER
        )
    """)

    conn.commit()

    # Auto-migration for Hebrew columns
    try:
        cursor.execute("SELECT team1_hebrew FROM matches LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE matches ADD COLUMN team1_hebrew TEXT")
            cursor.execute("ALTER TABLE matches ADD COLUMN team2_hebrew TEXT")
            conn.commit()
        except: pass

    conn.close()

def get_match_id(game_name, date):
    # Normalize ID: remove spaces, lowercase, add date
    clean_name = game_name.replace(" ", "").lower()
    return f"{clean_name}_{date}"

async def run_tracker():
    print("Initializing Database...")
    init_db()
    
    print("Scraping Winner for current odds...")
    winner = WinnerScraper(headless=True)
    winner_df = await winner.get_odds()
    
    if winner_df.empty:
        print("No data retrieved from Winner. Exiting.")
        return

    print(f"Retrieved {len(winner_df)} games from Winner.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
        
    cursor.execute("SELECT id, num_1, num_X, num_2, team1_hebrew, team2_hebrew FROM matches")
    existing_matches = {row[0]: {"1": row[1], "X": row[2], "2": row[3], "t1_he": row[4], "t2_he": row[5]} for row in cursor.fetchall()}

    new_matches_count = 0
    changed_matches_count = 0
    major_changes_count = 0

    from calculations import Game, check_favorite_flip, compare_games
    from message import major_change_notification, bet_notifications

    new_matches_df_rows = []
    
    print("Analyzing matches for changes...")
    for idx, row in winner_df.iterrows():
        match_id = get_match_id(row['game'], row['date'])
        
        # 1. New Match
        if match_id not in existing_matches:
            new_matches_count += 1
            new_matches_df_rows.append(row)
            cursor.execute("""
                INSERT INTO matches (id, game, date, team1, team2, team1_hebrew, team2_hebrew, num_1, num_X, num_2, link, league)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, row['game'], row['date'], row['team1'], row['team2'], row.get('team1_hebrew', ''), row.get('team2_hebrew', ''), row['num_1'], row['num_X'], row['num_2'], row['link'], row['league']))
            continue

        # 2. Existing Match - Check for changes
        old_odds = existing_matches[match_id]
        new_odds = {"1": row['num_1'], "X": row['num_X'], "2": row['num_2']}
        
        if old_odds['1'] != new_odds['1'] or old_odds['X'] != new_odds['X'] or old_odds['2'] != new_odds['2']:
            changed_matches_count += 1
            
            # Record in history
            cursor.execute("""
                INSERT INTO odds_history (match_id, old_1, old_X, old_2, new_1, new_X, new_2, change_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, old_odds['1'], old_odds['X'], old_odds['2'], new_odds['1'], new_odds['X'], new_odds['2'], "update"))
            
            # Update current state
            cursor.execute("""
                UPDATE matches SET num_1 = ?, num_X = ?, num_2 = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_odds['1'], new_odds['X'], new_odds['2'], match_id))

            # Check for Major Change (Favorite Flip) comparing Hebrew to Hebrew
            old_game = Game({
                "game": f"{old_odds.get('t1_he', row['team1'])} - {old_odds.get('t2_he', row['team2'])}",
                "date": row['date'],
                "num_1": old_odds['1'],
                "num_X": old_odds['X'],
                "num_2": old_odds['2'],
                "link": row['link']
            })
            new_game = Game({
                "game": f"{row.get('team1_hebrew', row['team1'])} - {row.get('team2_hebrew', row['team2'])}",
                "date": row['date'],
                "num_1": new_odds['1'],
                "num_X": new_odds['X'],
                "num_2": new_odds['2'],
                "link": row['link']
            })
            
            flip_res = check_favorite_flip(old_game, new_game, remote_name="New_Winner")
            
            if flip_res:
                major_changes_count += 1
                print(f"🚨 MAJOR CHANGE DETECTED for {row['game']}! Gap: {flip_res['gap']}")
                
                # Fetch Unibet/Pinnacle odds for major changes
                print("Fetching Unibet and Pinnacle context...")
                from scrapers.pinnacle import PinnacleScraper
                from scrapers.unibet import UnibetScraper
                
                # We need to fetch Unibet and Pinnacle
                try:
                    pinn_scraper = PinnacleScraper(headless=True)
                    unibet_scraper = UnibetScraper(headless=False)
                    
                    # Target specific Unibet league for this major change
                    unibet_target_leagues = None
                    if 'league' in row:
                        mapping = {}
                        try:
                            import os, json
                            base_dir = os.path.dirname(os.path.abspath(__file__))
                            map_path = os.path.join(base_dir, "winner_to_unibet_leagues.json")
                            if os.path.exists(map_path):
                                with open(map_path, "r", encoding="utf-8") as f:
                                    mapping = json.load(f)
                        except: pass
                        if row['league'] in mapping and mapping[row['league']]:
                            url = mapping[row['league']]
                            if "/betting/odds/" in url:
                                unibet_target_leagues = [url.split("/betting/odds/")[1]]
                    
                    results = await asyncio.gather(
                        pinn_scraper.get_odds(),
                        unibet_scraper.get_odds(leagues=unibet_target_leagues),
                        return_exceptions=True
                    )
                    
                    pinn_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
                    unibet_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
                    
                    # Single item DataFrame to test against
                    test_df = pd.DataFrame([row.to_dict()])
                    
                    # Run comparison to extract exact matching unibet/pinnacle row
                    unibet_opps = []
                    pinn_opps = []
                    
                    if not unibet_df.empty:
                        unibet_opps, _, _ = compare_games(test_df, unibet_df, remote_name="Unibet")
                    if not pinn_df.empty:
                        pinn_opps, _, _ = compare_games(test_df, pinn_df, remote_name="Pinnacle")
                        
                    alert_data = {
                        "game": row['game'],
                        "date": row['date'],
                        "old_winner_odds": old_odds,
                        "new_winner_odds": new_odds
                    }
                    
                    # Compare_games returns favorite_flip opportunities. If it matched, 
                    # we can extract the remote odds from the opportunity.
                    if unibet_opps:
                        alert_data['unibet_odds'] = unibet_opps[0].get('unibet_odds')
                    if pinn_opps:
                        alert_data['pinnacle_odds'] = pinn_opps[0].get('pinnacle_odds')
                        
                    major_change_notification(alert_data)
                    
                except Exception as e:
                    print(f"Error fetching remote odds for major change context: {e}")

    # Process New Matches exactly like regular bot
    if new_matches_df_rows:
        print(f"Processing {new_matches_count} brand new matches for standard arbitrage...")
        new_df = pd.DataFrame(new_matches_df_rows)
        
        try:
            from scrapers.pinnacle import PinnacleScraper
            from scrapers.unibet import UnibetScraper
            from message_state import should_send_notification, mark_notification_sent
            
            pinn_scraper = PinnacleScraper(headless=True)
            unibet_scraper = UnibetScraper(headless=False)
            
            # Optimization: Map new Winner leagues to Unibet target leagues
            unibet_target_leagues = None
            if 'league' in new_df.columns:
                active_leagues = new_df['league'].unique()
                mapping = {}
                try:
                    import os, json
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    map_path = os.path.join(base_dir, "winner_to_unibet_leagues.json")
                    if os.path.exists(map_path):
                        with open(map_path, "r", encoding="utf-8") as f:
                            mapping = json.load(f)
                except: pass

                unibet_target_leagues = []
                for l in active_leagues:
                    if l in mapping and mapping[l]:
                        url = mapping[l]
                        if "/betting/odds/" in url:
                            suffix = url.split("/betting/odds/")[1]
                            unibet_target_leagues.append(suffix)
                unibet_target_leagues = list(set(unibet_target_leagues)) if unibet_target_leagues else None
            
            print(f"Fetching standard Unibet (Targets: {len(unibet_target_leagues) if unibet_target_leagues else 'All'}) and Pinnacle odds for new matches...")
            results = await asyncio.gather(
                pinn_scraper.get_odds(),
                unibet_scraper.get_odds(leagues=unibet_target_leagues),
                return_exceptions=True
            )
            
            pinn_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
            unibet_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
            
            all_opportunities = []
            
            unmatched_new_df = new_df
            if not unibet_df.empty:
                print("Comparing New Matches vs Unibet...")
                unibet_opps, _, unibet_matched_indices = compare_games(new_df, unibet_df, remote_name="Unibet")
                all_opportunities.extend(unibet_opps)
                matched_indices_set = set(unibet_matched_indices)
                unmatched_new_df = new_df.iloc[[i for i in range(len(new_df)) if i not in matched_indices_set]]
                
            if not pinn_df.empty and not unmatched_new_df.empty:
                print(f"Comparing remaining {len(unmatched_new_df)} New Matches vs Pinnacle...")
                pinn_opps, _, _ = compare_games(unmatched_new_df, pinn_df, remote_name="Pinnacle")
                all_opportunities.extend(pinn_opps)
                
            for opp in all_opportunities:
                if should_send_notification(opp):
                    bet_notifications(odds_data=opp)
                    mark_notification_sent(opp)
                    
        except Exception as e:
            print(f"Error processing new matches for arbitrage: {e}")
            
    # Save RUN STATS
    cursor.execute("""
        INSERT INTO run_stats (total_matches, new_matches, changed_matches, major_changes, errors)
        VALUES (?, ?, ?, ?, ?)
    """, (len(winner_df), new_matches_count, changed_matches_count, major_changes_count, 0))
    
    conn.commit()
    conn.close()
    
    print(f"Run completed. Total: {len(winner_df)}, New: {new_matches_count}, Changed: {changed_matches_count}, Major: {major_changes_count}")

if __name__ == "__main__":
    try:
        asyncio.run(run_tracker())
    except Exception as e:
        print(f"Error in tracker: {e}")
