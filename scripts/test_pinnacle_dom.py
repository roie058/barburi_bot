import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
        )
        context = await b.new_context()
        pg = await context.new_page()
        
        print("Navigating to soccer matchups...")
        await pg.goto("https://www.pinnacle.com/en/soccer/matchups/", timeout=60000)
        
        print("Waiting for page to load...")
        await pg.wait_for_timeout(10000)
        
        await pg.screenshot(path="pinnacle_soccer_dom.png")
        print("Saved screenshot to pinnacle_soccer_dom.png")
        
        content = await pg.content()
        with open("pinnacle_dom.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved HTML to pinnacle_dom.html")
        
        await context.close()
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
