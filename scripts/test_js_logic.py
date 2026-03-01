import asyncio
from playwright.async_api import async_playwright

async def run_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://www.unibet.co.uk/betting/sports/filter/football/spain/la-liga"
        print(f"Navigating to {url}...")
        
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        try: await page.click("#onetrust-accept-btn-handler", timeout=3000)
        except: pass

        print("Scrolling...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        print("Dumping raw textContent of cards...")
        
        # Safe JS that returns array of strings
        data = await page.evaluate("""() => {
            const nodes = document.querySelectorAll('[data-test-name="contestCard"]');
            return Array.from(nodes).map(n => n.innerHTML);
        }""")
        
        print(f"Found {len(data)} cards.")
        for i, html in enumerate(data):
            # Check for Sociedad to minimize output noise
            if "Sociedad" in html:
                print(f"!!! FOUND TARGET HTML (Card {i}):")
                print(html[:1000]) # First 1000 chars of HTML
                break

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_debug())
