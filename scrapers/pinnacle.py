import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os
import json
import datetime

class PinnacleScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.base_url = "https://www.pinnacle.com/en/soccer/matchups/"

    async def get_odds(self):
        async with async_playwright() as p:
            print(f"Launching browser (headless={self.headless})...")
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            # Stealth measures
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            })

            try:
                # 1. Discover All Leagues
                leagues_url = "https://www.pinnacle.com/en/soccer/leagues"
                print(f"Navigating to {leagues_url} to discover leagues...")
                
                captured_leagues = []
                api_headers = {}
                
                async def handle_leagues(response):
                    if "leagues" in response.url and "matchups" not in response.url and "sports/29" in response.url:
                        try:
                            # Capture headers from the successful request to reuse
                            nonlocal api_headers
                            if not api_headers:
                                api_headers = await response.request.all_headers()
                            
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                                captured_leagues.extend(data)
                        except:
                            pass

                page.on("response", handle_leagues)
                await page.goto(leagues_url, timeout=60000)
                await page.wait_for_timeout(7000) # Increased wait for stability
                
                # Filter headers to remove problematic ones for fetch
                # We want to keep essential auth headers if they exist
                essential_headers = ['x-api-key', 'authorization', 'x-device-id', 'x-session-id']
                valid_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Referer": "https://www.pinnacle.com/"
                }

                if api_headers:
                    for k, v in api_headers.items():
                        kl = k.lower()
                        # Skip pseudo-headers (starting with :) which cause exceptions in manual fetch
                        if k.startswith(':'):
                            continue
                            
                        # Keep auth headers
                        if kl in essential_headers:
                            valid_headers[k] = v
                        # Keep other potentially useful headers but exclude browser-specifics that fetch handles
                        elif kl not in ['content-length', 'host', 'connection', 'accept-encoding', 'cookie', 'user-agent', 'referer', 'content-type']:
                            valid_headers[k] = v
                
                # Check for x-api-key, if not found, we might fail
                if 'x-api-key' not in [k.lower() for k in valid_headers.keys()]:
                    print("Warning: x-api-key not found in captured headers. Scraping might fail.")

                unique_leagues = {l['id']: l for l in captured_leagues if l.get('matchupCount', 0) > 0}
                print(f"Found {len(unique_leagues)} active leagues. Fetching matchups...")
                
                # 2. Fetch Matchups for EACH League
                all_raw_matches = []
                
                # Process in chunks to avoid overwhelming the browser/API
                league_ids = list(unique_leagues.keys())
                chunk_size = 5
                
                print(f"Using {len(valid_headers)} headers for Requests. Keys: {list(valid_headers.keys())}")

                all_data = {} # lid -> {matchups: [], markets: []}
                failed_calls = 0
                error_codes = {}

                # Use Playwright's APIRequestContext to fetch (bypasses CORS)
                async def fetch_league_matchups(lid):
                    url = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/matchups?brandId=0"
                    try:
                        resp = await page.request.get(url, headers=valid_headers)
                        if resp.status == 200:
                            return (lid, "matchups", await resp.json(), 200)
                        return (lid, "matchups", None, resp.status)
                    except Exception as e:
                        if "Exception" not in error_codes:
                             print(f"Sample Fetch Exception: {e}")
                        return (lid, "matchups", None, "Exception")

                async def fetch_league_markets(lid):
                    url = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{lid}/markets/straight?brandId=0"
                    try:
                        resp = await page.request.get(url, headers=valid_headers)
                        if resp.status == 200:
                            return (lid, "markets", await resp.json(), 200)
                        return (lid, "markets", None, resp.status)
                    except Exception as e:
                        return (lid, "markets", None, "Exception")

                for i in range(0, len(league_ids), chunk_size):
                    chunk = league_ids[i:i+chunk_size]
                    print(f"Fetching chunk {i // chunk_size + 1}/{len(league_ids) // chunk_size + 1}...")
                    
                    tasks = []
                    for lid in chunk:
                        tasks.append(fetch_league_matchups(lid))
                        tasks.append(fetch_league_markets(lid))
                    
                    results = await asyncio.gather(*tasks)
                    
                    for lid, kind, data, status in results:
                        if status != 200 or not data:
                            failed_calls += 1
                            error_codes[status] = error_codes.get(status, 0) + 1
                            continue
                        if lid not in all_data: all_data[lid] = {}
                        all_data[lid][kind] = data
                    
                    await asyncio.sleep(0.5)

                if failed_calls > 0:
                    print(f"Warning: {failed_calls} API calls failed. Error distribution: {error_codes}")

                print(f"Captured data for {len(all_data)} leagues. Processing...")
                
                # Debug dump markets for first league to verify structure
                first_lid = next(iter(all_data), None)
                if first_lid and "markets" in all_data[first_lid]:
                     with open("pinnacle_markets_debug.json", "w", encoding="utf-8") as f:
                        json.dump(all_data[first_lid]["markets"], f, indent=2)

                matches_dict = {}

                def convert_odds(price):
                    if price is None: return 0.0
                    if price > 0: return (price / 100) + 1
                    else: return (100 / abs(price)) + 1

                for lid, content in all_data.items():
                    matchups_data = content.get("matchups", [])
                    markets_data = content.get("markets", [])
                    
                    # Map markets by Matchup ID
                    # markets_data is a list of market objects
                    odds_map = {} # matchupId -> list of market objects
                    
                    m_list = []
                    if isinstance(markets_data, list):
                        m_list = markets_data
                    elif isinstance(markets_data, dict):
                         if "leagues" in markets_data:
                             for l in markets_data["leagues"]:
                                 if "matchups" in l: m_list.extend(l["matchups"])
                         elif "matchups" in markets_data:
                             m_list = markets_data["matchups"]
                    
                    for m in m_list:
                        m_id = m.get("id") or m.get("matchupId")
                        if m_id:
                            if m_id not in odds_map: odds_map[m_id] = []
                            odds_map[m_id].append(m)
                    
                    # Process Matchups
                    g_list = []
                    if isinstance(matchups_data, list): g_list = matchups_data
                    elif isinstance(matchups_data, dict):
                         if "matchups" in matchups_data: g_list = matchups_data["matchups"]
                         elif "leagues" in matchups_data: 
                             for l in matchups_data["leagues"]:
                                 if "matchups" in l: g_list.extend(l["matchups"])

                    for game in g_list:
                        if game.get("type", "") == "special": continue 
                        if "participants" not in game: continue
                        
                        g_id = game.get("id")
                        if g_id in matches_dict: continue

                        # Get Names
                        parts = game["participants"]
                        if len(parts) < 2: continue
                        
                        team1 = next((p["name"] for p in parts if p.get("alignment") == "home"), parts[0]["name"])
                        team2 = next((p["name"] for p in parts if p.get("alignment") == "away"), parts[1]["name"])

                        # Get Odds from Odds Map
                        game_markets = odds_map.get(g_id, [])
                        if not game_markets: continue # No odds found
                        
                        # Find Full Time Moneyline (Period 0, Type moneyline)
                        ml_market = next((m for m in game_markets if m.get("period") == 0 and m.get("type") == "moneyline"), None)
                        
                        if not ml_market: continue

                        prices = ml_market.get("prices", [])
                        if not prices: continue

                        p1 = next((p["price"] for p in prices if p.get("designation") == "home"), None)
                        p2 = next((p["price"] for p in prices if p.get("designation") == "away"), None)
                        pX = next((p["price"] for p in prices if p.get("designation") == "draw"), None)

                        if p1 is None or p2 is None: continue 
                        
                        matches_dict[g_id] = {
                            "game": f"{team1} - {team2}",
                            "date": game.get("startTime", ""),
                            "num_1": round(convert_odds(p1), 2),
                            "num_X": round(convert_odds(pX), 2) if pX else 0.0,
                            "num_2": round(convert_odds(p2), 2),
                            "link": f"https://www.pinnacle.com/en/soccer/leagues/{lid}"
                        }

                matches = list(matches_dict.values())
                print(f"Successfully scraped {len(matches)} matches from ALL leagues.")
                # Save scraped data for inspection
                pd.DataFrame(matches).to_csv("pinnacle_all_matches.csv", index=False)
                return pd.DataFrame(matches)

            except Exception as e:
                print(f"Error scraping Pinnacle: {e}")
                # Return empty DataFrame on error if needed or list
                return []
            finally:
                await browser.close()

if __name__ == "__main__":
    scraper = PinnacleScraper(headless=True)
    results = asyncio.run(scraper.get_odds())
    print(results[:5])
