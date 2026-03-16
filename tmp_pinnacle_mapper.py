import json
import asyncio
import re
from difflib import get_close_matches
from playwright.async_api import async_playwright

async def get_pinnacle_leagues():
    captured_leagues = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        
        async def handle_response(response):
            if "sports/29/leagues" in response.url:
                try:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                        captured_leagues.extend([d['name'] for d in data])
                except Exception as e:
                    print("Error parsing leagues JSON:", e)
                    
        page.on("response", handle_response)
        print("Fetching Pinnacle leagues...")
        await page.goto("https://www.pinnacle.com/en/soccer/leagues", timeout=60000)
        await page.wait_for_timeout(5000)
        await browser.close()
    return list(set(captured_leagues))

def extract_unibet_keywords(url):
    if not url or "unibet" not in url: return ""
    # "https://www.unibet.co.uk/betting/odds/football/england/premier-league" -> "england premier league"
    parts = url.split("/football/")
    if len(parts) > 1:
        clean = parts[1].replace("-", " ").replace("/", " ")
        return clean
    return ""

async def main():
    pinnacle_names = await get_pinnacle_leagues()
    if not pinnacle_names:
        print("Failed to fetch Pinnacle leagues from API.")
        return
        
    print(f"Fetched {len(pinnacle_names)} active leagues from Pinnacle.")
    pinnacle_lower_map = {name.lower().replace("-", " "): name for name in pinnacle_names}
    
    with open("winner_to_unibet_leagues.json", "r", encoding="utf-8") as f:
        unibet_map = json.load(f)
        
    try:
        with open("winner_to_pinnacle_leagues.json", "r", encoding="utf-8") as f:
            pinnacle_map = json.load(f)
    except:
        pinnacle_map = {}
        
    matched_count = 0
    
    for heb_name, unibet_url in unibet_map.items():
        if heb_name in pinnacle_map and pinnacle_map[heb_name]:
            continue # Already mapped
            
        search_term = extract_unibet_keywords(unibet_url)
        if not search_term: continue
        
        # Exact/Substring Match First
        best_match = None
        for p_clean, p_orig in pinnacle_lower_map.items():
            if search_term == p_clean or search_term in p_clean or p_clean in search_term:
                best_match = p_orig
                break
                
        # Diff match if no exact
        if not best_match:
            close = get_close_matches(search_term, pinnacle_lower_map.keys(), n=1, cutoff=0.6)
            if close:
                best_match = pinnacle_lower_map[close[0]]
                
        if best_match:
            print(f"Mapped: {heb_name} -> {best_match} (via '{search_term}')")
            pinnacle_map[heb_name] = best_match
            matched_count += 1
            
    with open("winner_to_pinnacle_leagues.json", "w", encoding="utf-8") as f:
        json.dump(pinnacle_map, f, ensure_ascii=False, indent=4)
        
    print(f"\nSuccessfully auto-mapped {matched_count} new Pinnacle leagues.")

if __name__ == "__main__":
    asyncio.run(main())
