
import asyncio
from playwright.async_api import async_playwright
import json

async def research_api():
    async with async_playwright() as p:
        # Launch non-headless to bypass initial bots if needed, though headless with args might work
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        captured_requests = []
        
        # Monitor Network Traffic
        async def handle_response(response):
            try:
                # Kambi APIs often have 'kambio' or 'cdn' or 'offering' in the URL
                # and return JSON
                if "json" in response.headers.get("content-type", ""):
                    url = response.url
                    # Broaden filter to catch Kambi/KambiCDN
                    if any(x in url for x in ["kambi", "offering", "events", "betting", "cdn", "api"]):
                        print(f"Captured JSON URL: {url}")
                        try:
                            data = await response.json()
                            captured_requests.append({
                                "url": url,
                                "data": data
                            })
                        except:
                            pass
            except:
                pass

        page.on("response", handle_response)
        
        print("Navigating to Unibet Premier League page...")
        await page.goto("https://www.unibet.co.uk/betting/sports/filter/football/england/premier_league", timeout=60000)
        
        print("Waiting for data to load...")
        await page.wait_for_timeout(10000)
        
        print(f"Captured {len(captured_requests)} JSON responses.")
        
        # Analyze captured data
        found_data = False
        for req in captured_requests:
            data = req['data']
            url = req['url']
            
            # Look for match data (team names)
            s_data = json.dumps(data)
            if "Arsenal" in s_data or "Liverpool" in s_data:
                print(f"FOUND MATCH DATA IN: {url}")
                found_data = True
                
                # Save this JSON for inspection
                filename = "unibet_api_sample.json"
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"Saved sample data to {filename}")
                break
        
        if not found_data:
            print("Did not find match data in captured JSONs. Checking for 'events' key...")
             # Check for generic event lists
            for req in captured_requests:
                data = req['data']
                if isinstance(data, dict) and "events" in data:
                    print(f"Found 'events' key in: {req['url']}")
                    with open("unibet_api_events.json", "w") as f:
                        json.dump(data, f, indent=2)
                    break
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_api())
