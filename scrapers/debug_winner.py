import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Headless False to see if it helps? No, CI environment usually forbids it. Keep it True or try False if allowed. User said "windows", so maybe? But better stick to True for stability.
        # Actually User has windows, so I can use headless=True.
        # But wait, maybe headless detection is blocking the API?
        # I'll stick to True but add stealth args if possible.
        
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        page.on("request", lambda request: print(f"Request: {request.url}"))
        
        print("Navigating...")
        await page.goto("https://www.winner.co.il/games/winner-line/today/", timeout=60000)
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
