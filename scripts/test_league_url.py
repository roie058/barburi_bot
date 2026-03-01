import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
        )
        c = await b.new_context()
        pg = await c.new_page()
        
        url = 'https://www.pinnacle.com/en/soccer/matchups/'
        print(f"Testing URL: {url}")
        
        try:
            await pg.goto(url, timeout=30000)
            await pg.wait_for_timeout(8000)
            links = await pg.query_selector_all("a[href]")
            urls = []
            for l in links:
                href = await l.get_attribute('href')
                if href and '/soccer/' in href and href not in urls:
                    urls.append(href)
            print("Found Soccer URLs:")
            for u in urls:
                if 'matchup' in u.lower() or 'league' in u.lower():
                    print(u)
        except Exception as e:
            print(f"Failed: {e}")
            
        await b.close()

if __name__ == '__main__':
    asyncio.run(test())
