import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        captured_data = []

        async def handle_response(response):
            if "MobileLine" in response.url or "winner-line" in response.url:
                try:
                    # Filter only JSON responses
                    ct = response.headers.get("content-type", "")
                    if "application/json" in ct:
                        data = await response.json()
                        captured_data.append(data)
                        print(f"Captured data from {response.url}")
                except:
                    pass

        page.on("response", handle_response)
        
        print("Navigating to Winner...")
        try:
            await page.goto("https://www.winner.co.il/games/winner-line/today/", timeout=60000)
            
            # Scroll a bit to trigger loading
            print("Scrolling...")
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            
            print("Processing captured data...")
            unique_leagues = set()
            
            # Analyze captured JSONs
            for chunk in captured_data:
                # Structure might be list of dicts or dict with markets
                items = []
                if isinstance(chunk, list):
                    items = chunk
                elif isinstance(chunk, dict) and "markets" in chunk:
                    items = chunk["markets"]
                elif isinstance(chunk, dict):
                     items = [chunk]

                for item in items:
                    # Look for league/tournament fields
                    # Common fields often contain "league", "league_name", "category", "tournament"
                    # Based on standard betting APIs, might be "c_name" (category), "t_name" (tournament), "l_name"
                    
                    # Dump keys of first item to see structure
                    # print(item.keys())
                    
                    possible_keys = ["league_name", "league", "tournament_name", "tournament", "tn", "cn", "c_name", "t_name", "s_name"]
                    
                    found_league = None
                    for k in item.keys():
                        if k in possible_keys:
                            found_league = item[k]
                            break
                    
                    # Sometimes it's nested
                    if not found_league:
                        # Try to find hebrew text strings in values that look like leagues
                        pass

                    # Let's just save the raw keys and some sample data to a file to inspect manually first
                    # or filter by known fields if we find them.
                    
                    # "m_code" - match code?
                    # "mp" - marketing name (e.g. "Result 1X2")
                    # "desc" - Team A - Team B
                    
                    # Winner specific: 'l_desc' often holds league description?
                    if 'l_desc' in item:
                         unique_leagues.add(item['l_desc'])
                    elif 'league' in item:
                         unique_leagues.add(item['league'])
            
            print(f"Found {len(unique_leagues)} unique leagues.")
            for l in unique_leagues:
                print(f" - {l}")
                
            # Save raw sample for inspection
            os.makedirs("logs", exist_ok=True)
            with open("logs/winner_raw_sample.json", "w", encoding="utf-8") as f:
                json.dump(captured_data, f, indent=2, ensure_ascii=False)
            print("Saved raw data to logs/winner_raw_sample.json")
            
            # Save extracted leagues
            with open("logs/extracted_winner_leagues.txt", "w", encoding="utf-8") as f:
                 for l in sorted(unique_leagues):
                     f.write(l + "\n")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
