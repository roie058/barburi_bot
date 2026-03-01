import asyncio
from playwright.async_api import async_playwright

async def debug_drawer():
    async with async_playwright() as p:
        # HEADFUL MODE to replicate main run behavior
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Premier League - Check for Jan 26
        url = "https://www.unibet.co.uk/betting/sports/filter/football/england/premier_league"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            # Cookie?
            try: await page.click("#onetrust-accept-btn-handler", timeout=3000)
            except: pass
            
            await asyncio.sleep(3) 

            # DEEP SCROLL
            print("Scrolling deeply (50x)...")
            for i in range(50):
                await page.keyboard.press("End")
                await asyncio.sleep(0.5)
                if i % 10 == 0: print(f"Scroll {i}...")

            # Expand Headers
            print("Expanding headers...")
            await page.evaluate("""() => {
               const dateHeaders = document.querySelectorAll('[data-test-name="MainHeader"], [data-test-name="match-group-header"]');
               dateHeaders.forEach(h => {
                    if (h.getAttribute('aria-expanded') !== 'true') {
                         h.click(); 
                    }
               });
            }""")
            await asyncio.sleep(5)
            
            # Inspect Headers (Broad Search)
            print("Inspecting ALL potential date headers...")
            header_dump = await page.evaluate("""() => {
                const allOver = Array.from(document.querySelectorAll('[data-test-name="MainHeader"], [data-test-name="match-group-header"]'));
                return allOver.map(c => ({
                    text: c.innerText,
                    expanded: c.getAttribute('aria-expanded')
                }));
            }""")
            
            found_jan_26 = False
            for h in header_dump:
                print(f"Header: {h}")
                if "26" in h['text'] and "Jan" in h['text']:
                    found_jan_26 = True
                    
            if found_jan_26:
                print("SUCCESS: Found Jan 26 Header!")
            else:
                print("FAILURE: Jan 26 Header NOT found.")

            # Count games visible
            print("Extracting game names...")
            games = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('[data-test-name="contestCard"]')).map(c => {
                    const lines = c.innerText.split('\\n');
                    return lines[0] + " - " + (lines[1] || ""); 
                });
            }""")
            
            print(f"Visible Games (Headful): {len(games)}")
            for g in games:
                print(f"GAME: {g}")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_drawer())
