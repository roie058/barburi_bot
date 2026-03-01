import asyncio
from playwright.async_api import async_playwright

async def run_debug():
    async with async_playwright() as p:
        # Headful for stability/debugging
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        
        url = "https://www.unibet.co.uk/betting/sports/filter/football/spain/la-liga"
        print(f"Navigating to {url}...")
        
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        try: await page.click("#onetrust-accept-btn-handler", timeout=3000)
        except: pass

        # Scroll deeply first
        print("Scrolling to load data (20x)...")
        for i in range(20):
            await page.keyboard.press("End")
            await asyncio.sleep(0.5)
            if i % 5 == 0: print(f"Scroll {i}...")
        
        await asyncio.sleep(2)

        # CHECK 1: Search for "Sociedad" in the raw text content of the body
        print("Checking document.body.textContent for 'Sociedad'...")
        found_text = await page.evaluate("document.body.textContent.includes('Sociedad')")
        print(f"Found 'Sociedad' in textContent? {found_text}")

        # CHECK 2: Count contestCards
        print("Counting Match Cards...")
        counts = await page.evaluate("""() => {
            const cards = document.querySelectorAll('[data-test-name="contestCard"]');
            let visibleCount = 0;
            let hiddenCount = 0;
            
            cards.forEach(c => {
                // Check visibility using offsetParent (standard check) or styling
                const style = window.getComputedStyle(c);
                if (c.offsetParent === null || style.display === 'none' || style.visibility === 'hidden') {
                    hiddenCount++;
                } else {
                    visibleCount++;
                }
            });
            return { total: cards.length, visible: visibleCount, hidden: hiddenCount };
        }""")
        print(f"Card Counts: {counts}")

        # CHECK 3: Try to extract a hidden card using textContent vs innerText
        # Find a parent that is closed (e.g. aria-expanded=false) and check if it has cards inside in DOM
        print("Checking Closed Headers for Hidden Data...")
        hidden_data_check = await page.evaluate("""() => {
             const headers = Array.from(document.querySelectorAll('[data-test-name="MainHeader"], [data-test-name="match-group-header"]'));
             const closedHeader = headers.find(h => h.getAttribute('aria-expanded') !== 'true');
             
             if (!closedHeader) return "All headers are open (unexpected for deep scroll)";
             
             // Look for siblings or children that might contain match data
             // Usually the drawer content is a sibling div
             let sibling = closedHeader.nextElementSibling;
             let foundCard = false;
             let texts = {};
             
             // Check next 5 siblings
             for(let i=0; i<5; i++) {
                 if(!sibling) break;
                 if(sibling.innerHTML.includes('contestCard')) {
                     foundCard = true;
                     texts.innerText = sibling.innerText;
                     texts.textContent = sibling.textContent;
                     break;
                 }
                 sibling = sibling.nextElementSibling;
             }
             
             return {
                 header: closedHeader.innerText,
                 foundCardInDom: foundCard,
                 content: texts
             };
        }""")
        print(f"Closed Header Analysis: {hidden_data_check}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_debug())
