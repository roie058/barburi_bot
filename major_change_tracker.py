import sqlite3
import pandas as pd
import asyncio
import os
import time
import json
from datetime import datetime

from scrapers.winner import WinnerScraper
from mapping_manager import mapping_manager
from stats_manager import StatsManager

DB_PATH = "data/tracker.sqlite"
stats = StatsManager()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
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
    
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    cursor = conn.cursor()
        
    cursor.execute("SELECT id, num_1, num_X, num_2, team1_hebrew, team2_hebrew FROM matches")
    existing_matches = {row[0]: {"1": row[1], "X": row[2], "2": row[3], "t1_he": row[4], "t2_he": row[5]} for row in cursor.fetchall()}

    new_matches_count = 0
    changed_matches_count = 0
    major_changes_count = 0

    from calculations import Game, check_favorite_flip, compare_games
    from message import major_change_notification, bet_notifications

    new_matches_df_rows = []
    major_change_games = []
    
    # Needs Unibet / Pinnacle data?
    leagues_needing_remote_check = set()

    print("Analyzing matches for changes...")
    for idx, row in winner_df.iterrows():
        match_id = get_match_id(row['game'], row['date'])
        
        # 1. New Match
        if match_id not in existing_matches:
            new_matches_count += 1
            new_matches_df_rows.append(row)
            stats.add_new_games(1)
            cursor.execute("""
                INSERT INTO matches (id, game, date, team1, team2, team1_hebrew, team2_hebrew, num_1, num_X, num_2, link, league)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, row['game'], row['date'], row['team1'], row['team2'], row.get('team1_hebrew', ''), row.get('team2_hebrew', ''), row['num_1'], row['num_X'], row['num_2'], row['link'], row['league']))
            
            if 'league' in row and pd.notna(row['league']):
                leagues_needing_remote_check.add(row['league'])
            continue

        # 2. Existing Match - Check for changes
        old_odds = existing_matches[match_id]
        new_odds = {"1": row['num_1'], "X": row['num_X'], "2": row['num_2']}
        
        if old_odds['1'] != new_odds['1'] or old_odds['X'] != new_odds['X'] or old_odds['2'] != new_odds['2']:
            changed_matches_count += 1
            stats.add_games_changed(1)
            
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
                major_change_games.append({
                    "row": row,
                    "old_odds": old_odds,
                    "new_odds": new_odds
                })
                if 'league' in row and pd.notna(row['league']):
                    leagues_needing_remote_check.add(row['league'])

    # IMPORTANT: Commit the transaction here to release the SQLite write lock!
    # The upcoming remote scraping can take 5+ minutes, and we don't want to block the database.
    conn.commit()

    # --- BATCH FETCH UNIBET & PINNACLE ONCE ---
    unibet_df = pd.DataFrame()
    pinn_df = pd.DataFrame()

    if new_matches_df_rows or major_change_games:
        print(f"Fetching remote data for {len(leagues_needing_remote_check)} required leagues...")
        from scrapers.pinnacle import PinnacleScraper
        from scrapers.unibet import UnibetScraper
        
        pinn_scraper = PinnacleScraper(headless=True)
        unibet_scraper = UnibetScraper(headless=False)
        
        unibet_target_leagues = []
        missing_unibet_leagues = []
        pinnacle_target_leagues = []
        missing_pinnacle_leagues = []
        
        if leagues_needing_remote_check:
            # 1. Map Unibet
            mapping_unibet = {}
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                map_path_u = os.path.join(base_dir, "winner_to_unibet_leagues.json")
                if os.path.exists(map_path_u):
                    with open(map_path_u, "r", encoding="utf-8") as f:
                        mapping_unibet = json.load(f)
            except Exception as e:
                print(f"Error loading Unibet mapping: {e}")

            if not mapping_unibet:
                print(f"WARNING: mapping_unibet is empty. Either the file doesn't exist, is empty, or failed to parse.")

            for l in leagues_needing_remote_check:
                if l in mapping_unibet and mapping_unibet[l]:
                    url = mapping_unibet[l]
                    if "/betting/odds/" in url:
                        suffix = url.split("/betting/odds/")[1]
                        unibet_target_leagues.append(suffix)
                else:
                    missing_unibet_leagues.append(l)
                    
            # 2. Map Pinnacle
            mapping_pinnacle = {}
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                map_path_p = os.path.join(base_dir, "winner_to_pinnacle_leagues.json")
                if os.path.exists(map_path_p):
                    with open(map_path_p, "r", encoding="utf-8") as f:
                        mapping_pinnacle = json.load(f)
                else:
                    print(f"ERROR: Pinnacle mapping file not found at {map_path_p}")
            except Exception as e:
                print(f"Error loading Pinnacle mapping: {e}")
            
            for l in leagues_needing_remote_check:
                if l in mapping_pinnacle and mapping_pinnacle[l]:
                    pinnacle_target_leagues.append(mapping_pinnacle[l])
                else:
                    missing_pinnacle_leagues.append(l)
                        
        unibet_target_leagues = list(set(unibet_target_leagues))
        pinnacle_target_leagues = list(set(pinnacle_target_leagues))
        
        if missing_unibet_leagues:
            print(f"⚠️ Missing Unibet Mapping for {len(missing_unibet_leagues)} leagues. Please add them to winner_to_unibet_leagues.json: {missing_unibet_leagues}")
            stats.set_leagues_needing_mapping(len(missing_unibet_leagues) + len(missing_pinnacle_leagues))
            # Append only unique missing leagues
            os.makedirs('reports', exist_ok=True)
            existing = set()
            if os.path.exists('reports/missing_unibet_leagues.md'):
                with open('reports/missing_unibet_leagues.md', 'r', encoding='utf-8') as f:
                    existing = {line.strip().replace('- ', '') for line in f if line.strip().startswith('- ')}
            with open('reports/missing_unibet_leagues.md', 'a', encoding='utf-8') as f:
                for l in missing_unibet_leagues:
                    if l not in existing:
                        f.write(f"- {l}\n")
                        existing.add(l)
                    
        if missing_pinnacle_leagues:
            print(f"⚠️ Missing Pinnacle Mapping for {len(missing_pinnacle_leagues)} leagues. Please add them to winner_to_pinnacle_leagues.json: {missing_pinnacle_leagues}")
            # Append only unique missing leagues
            os.makedirs('reports', exist_ok=True)
            existing_pin = set()
            if os.path.exists('reports/missing_pinnacle_leagues.md'):
                with open('reports/missing_pinnacle_leagues.md', 'r', encoding='utf-8') as f:
                    existing_pin = {line.strip().replace('- ', '') for line in f if line.strip().startswith('- ')}
            with open('reports/missing_pinnacle_leagues.md', 'a', encoding='utf-8') as f:
                for l in missing_pinnacle_leagues:
                    if l not in existing_pin:
                        f.write(f"- {l}\n")
                        existing_pin.add(l)
        
        # We MUST NOT pass None to unibet, otherwise it scrapes all mapped leagues!
        # If unibet_target_leagues is empty, passing [] makes Unibet skip scraping (it returns empty quickly)
        print(f"Mapped to {len(unibet_target_leagues)} Unibet leagues.")
        print(f"Mapped to {len(pinnacle_target_leagues)} Pinnacle leagues.")
        
        try:
            results = await asyncio.gather(
                pinn_scraper.get_odds(leagues=pinnacle_target_leagues),
                unibet_scraper.get_odds(leagues=unibet_target_leagues),
                return_exceptions=True
            )
            pinn_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
            unibet_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
        except Exception as e:
            print(f"Error fetching remote data: {e}")

        # Name Inference
        in_u = mapping_manager.infer_mappings(winner_df, unibet_df, "Unibet", "Unibet Inference")
        in_p = mapping_manager.infer_mappings(winner_df, pinn_df, "Pinnacle", "Pinnacle Inference")
        if in_u or in_p:
            print(f"Tracker Context Inference: Deduced {in_u} names from Unibet and {in_p} from Pinnacle.")
            stats.add_names_inferred(in_u + in_p)

    # Process Major Changes
    for mc in major_change_games:
        row = mc['row']
        old_odds = mc['old_odds']
        new_odds = mc['new_odds']
        
        test_df = pd.DataFrame([row.to_dict()])
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
        
        if unibet_opps:
            alert_data['unibet_odds'] = unibet_opps[0].get('unibet_odds')
        if pinn_opps:
            alert_data['pinnacle_odds'] = pinn_opps[0].get('pinnacle_odds')
            
        major_change_notification(alert_data)

    # Process New Matches exactly like regular bot
    if new_matches_df_rows:
        print(f"Processing {new_matches_count} brand new matches for standard arbitrage...")
        new_df = pd.DataFrame(new_matches_df_rows)
        
        try:
            from message_state import should_send_notification, mark_notification_sent
            
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
    
    # Save Last Run Telemetry
    u_matched_rough = sum(1 for _, row in unibet_df.iterrows() if row.get("game") in [mapping_manager.get_translation(wg) for wg in winner_df["game"]]) if not unibet_df.empty else 0
    p_matched_rough = sum(1 for _, row in pinn_df.iterrows() if row.get("game") in [mapping_manager.get_translation(wg) for wg in winner_df["game"]]) if not pinn_df.empty else 0
    stats.set_last_run_success(
        len(winner_df), 
        len(unibet_df) if not unibet_df.empty else 0, 
        len(pinn_df) if not pinn_df.empty else 0,
        u_matched_rough,
        p_matched_rough
    )
    
    print(f"Run completed. Total: {len(winner_df)}, New: {new_matches_count}, Changed: {changed_matches_count}, Major: {major_changes_count}")

async def main_loop():
    import random
    import traceback
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting tracking cycle...")
            await run_tracker()
        except Exception as e:
            print(f"Critical error in main loop: {e}")
            stats.set_last_run_failed(str(e))
            traceback.print_exc() # Print full traceback for debugging
            
        jitter_seconds = random.randint(180, 420)
        delay_minutes = jitter_seconds / 60.0
        print(f"Cycle finished. Sleeping for {delay_minutes:.2f} minutes ({jitter_seconds} seconds) to evade bot detection...")
        await asyncio.sleep(jitter_seconds)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nTracker stopped by user.")
    except Exception as e:
        print(f"Fatal tracker error: {e}")
