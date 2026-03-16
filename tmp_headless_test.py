import asyncio
from playwright.async_api import async_playwright

async def run_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        url = "https://www.unibet.co.uk/betting/sports/filter/football/spain/la-liga"
        print(f"Navigating to {url}...")
        
        await page.goto(url, timeout=60000)
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except:
            print("wait_for_load_state timeout")
            pass
            
        print("Waiting 5s for hydration...")
        await asyncio.sleep(5)
        
        print("Scrolling...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(5)
        
        data = await page.evaluate("""() => {
            const nodes = document.querySelectorAll('[data-test-name="contestCard"]');
            return Array.from(nodes).map(n => n.innerHTML);
        }""")
        
        print(f"Found {len(data)} cards.")
        
        with open("tmp_unibet_headless.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        await browser.close()

asyncio.run(run_debug())
