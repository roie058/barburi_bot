import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
        )
        context = await b.new_context(record_har_path="pinnacle.har")
        pg = await context.new_page()
        
        valid_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.pinnacle.com/",
            "Origin": "https://www.pinnacle.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }
        
        url_matchups = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/1980/matchups?brandId=0"
        url_markets = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/1980/markets/straight?brandId=0"
        
        print("Fetching matchups for 1980...")
        resp_m = await pg.request.get(url_matchups, headers=valid_headers)
        print(f"Matchups Status: {resp_m.status}")
        if resp_m.status == 200:
            with open("test_matchups_1980.json", "w", encoding="utf-8") as f:
                json.dump(await resp_m.json(), f, indent=2)
                
        print("Fetching markets for 1980...")
        resp_mk = await pg.request.get(url_markets, headers=valid_headers)
        print(f"Markets Status: {resp_mk.status}")
        if resp_mk.status == 200:
            with open("test_markets_1980.json", "w", encoding="utf-8") as f:
                json.dump(await resp_mk.json(), f, indent=2)
                
        await context.close()
        await b.close()
        print("Done.")
        print("Done. Saved to pinnacle.har")

if __name__ == "__main__":
    asyncio.run(main())
