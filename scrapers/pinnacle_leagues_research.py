import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Stealth
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        })

        async def handle_response(response):
            # We are looking for the list of leagues
            if "leagues" in response.url and "matchups" not in response.url:
                print(f"Potential League List API: {response.url}")
                try:
                    data = await response.json()
                    # Check if it looks like a list of leagues (has 'id', 'name', 'matchupCount')
                    is_league_list = False
                    if isinstance(data, list) and len(data) > 0 and "id" in data[0] and "name" in data[0]:
                        is_league_list = True
                    elif isinstance(data, dict):
                         # Maybe wrapped?
                         pass
                    
                    if is_league_list:
                        print(f"Captured League List with {len(data)} items.")
                        with open("pinnacle_leagues_list.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                except:
                    pass

        page.on("response", handle_response)
        
        url = "https://www.pinnacle.com/en/soccer/leagues"
        print(f"Navigating to {url}...")
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
