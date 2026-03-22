import asyncio
import json
import os
import random
import pandas as pd
from playwright.async_api import async_playwright
from deep_translator import GoogleTranslator
from scrapers.stealth_config import (
    STEALTH_ARGS, get_context_options, apply_stealth,
    human_delay, human_scroll
)
from mapping_manager import mapping_manager

class WinnerScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.base_url = "https://www.winner.co.il"

    async def get_translation(self, text):
        from_manager = mapping_manager.get_translation(text)
        if from_manager:
            return from_manager
        
        try:
             translated = GoogleTranslator(source='iw', target='en').translate(text)
             if translated:
                mapping_manager.save_pending(text, translated, "Translated")
                return translated
             return text
        except Exception:
            return text

    async def get_odds(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=STEALTH_ARGS
            )
            context = await browser.new_context(
                **get_context_options(locale="he-IL", timezone="Asia/Jerusalem")
            )
            page = await context.new_page()
            await apply_stealth(page)
            
            captured_data = []

            async def handle_response(response):
                if dict(response.headers).get("content-type", "").find("application/json") > -1 or "MobileLine" in response.url:
                   if "MobileLine" in response.url:
                        try:
                            data = await response.json()
                            if isinstance(data, list) or (isinstance(data, dict) and len(str(data)) > 1000):
                                captured_data.append(data)
                        except:
                            pass

            page.on("response", handle_response)
            
            try:
                target_url = "https://www.winner.co.il/games/winner-line/today/"
                print(f"Navigating to {target_url}...")
                await page.goto(target_url, timeout=60000)
                
                print("Scrolling to load more matches...")
                await human_scroll(page, scroll_count=random.randint(8, 12))
                
                await human_delay(1800, 500)
                
                if not captured_data:
                    print("No useful data found in intercepted responses.")
                    return pd.DataFrame()
                
                print(f"Captured {len(captured_data)} JSONs. Processing all...")
                
                all_matches = []
                seen_event_keys = set() 
                duplicates_log = []
                
                # 1. Total Raw Entries count
                total_raw_entries = 0
                for chunk in captured_data:
                    if isinstance(chunk, list): total_raw_entries += len(chunk)
                    elif isinstance(chunk, dict) and "markets" in chunk: total_raw_entries += len(chunk["markets"])

                # 2. Pre-filter valid 1X2 games
                valid_games = []
                for chunk in captured_data:
                    items = []
                    if isinstance(chunk, list): items = chunk
                    elif isinstance(chunk, dict) and "markets" in chunk: items = chunk["markets"]
                    
                    for game in items:
                        market_name = game.get("mp", "")
                        clean_mp = market_name.replace('\u200e', '').replace('\u202c', '').replace('\u202b', '')
                        
                        if "1X2" not in clean_mp and "תוצאת סיום" not in clean_mp:
                            continue
                        
                        exclude_terms = ["מחצית", "יותר", "פחות", "שערים", "קרנות", "כרטיסים", "כפול", "יתרון", "Handicap"]
                        if any(term in clean_mp for term in exclude_terms):
                            continue
                        
                        outcomes = game.get("outcomes", [])
                        if len(outcomes) != 3:
                            continue
                        
                        desc = game.get("desc", "")
                        if " - " not in desc:
                            continue
                        
                        valid_games.append(game)
                
                print(f"Found {len(valid_games)} valid 1X2 games out of {total_raw_entries} raw entries.")
                print(f"Translating and processing {len(valid_games)} match entries...")
                
                processed_count = 0
                duplicates_count = 0
                invalid_odds_count = 0

                for game in valid_games:
                    desc = game.get("desc", "")
                    clean_desc = desc.replace('\u200e', '').replace('\u202c', '').replace('\u202b', '')
                    
                    parts = clean_desc.split(" - ")
                    team1_he = parts[0].strip()
                    team2_he = parts[-1].strip()
                    
                    e_date = str(game.get("e_date", ""))
                    match_key = (e_date, team1_he, team2_he)
                    
                    if match_key in seen_event_keys:
                        duplicates_count += 1
                        duplicates_log.append(f"| {e_date} | {team1_he} - {team2_he} | Exact match key already processed |")
                        continue
                    seen_event_keys.add(match_key)
                    
                    outcomes = game.get("outcomes", [])
                    try:
                        odd1 = float(outcomes[0]['price'])
                        oddX = float(outcomes[1]['price'])
                        odd2 = float(outcomes[2]['price'])
                    except (ValueError, IndexError):
                        invalid_odds_count += 1
                        continue
                    
                    # Translate
                    team1_en = await self.get_translation(team1_he)
                    team2_en = await self.get_translation(team2_he)
                    
                    if processed_count % 20 == 0 or processed_count == len(valid_games):
                        print(f"Processed {processed_count}/{len(valid_games)} valid matches...")
                    
                    processed_count += 1
                    
                    league_name = game.get("l_desc") or game.get("league", "")

                    all_matches.append({
                        "game": f"{team1_en} - {team2_en}",
                        "hebrew_game": f"{team1_he} - {team2_he}",
                        "date": e_date,
                        "num_1": odd1,
                        "num_X": oddX,
                        "num_2": odd2,
                        "link": self.base_url,
                        "team1": team1_en,
                        "team2": team2_en,
                        "team1_hebrew": team1_he,
                        "team2_hebrew": team2_he,
                        "league": league_name
                    })
                
                if duplicates_count > 0 or invalid_odds_count > 0:
                    print(f"Notes: Skipped {duplicates_count} duplicates and {invalid_odds_count} games with invalid odds.")
                    
                    if duplicates_log:
                        os.makedirs("reports", exist_ok=True)
                        with open("reports/winner_duplicates.md", "w", encoding="utf-8") as f:
                            f.write("# Winner Scraper - Duplicate Games Report\n")
                            f.write(f"Generated at: {pd.Timestamp.now()}\n")
                            f.write(f"Total Duplicates: {len(duplicates_log)}\n\n")
                            f.write("| Date | Game (Hebrew) | Reason |\n")
                            f.write("|---|---|---|\n")
                            for line in duplicates_log:
                                f.write(line + "\n")
                        print(" Detailed duplicate report saved to reports/winner_duplicates.md")

                df_matches = pd.DataFrame(all_matches)
                print(f"Winner Scraper finished. Total matches: {len(df_matches)}")
                
                os.makedirs("logs", exist_ok=True)
                df_matches.to_csv("logs/winner_matches.csv", index=False)
                return df_matches

            except Exception as e:
                print(f"Error scraping Winner: {e}")
                return pd.DataFrame()
            finally:
                await browser.close()
