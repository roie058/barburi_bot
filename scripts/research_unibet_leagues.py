
import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def find_leagues():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        # Unibet "All Football" or "Browse" page
        url = "https://www.unibet.co.uk/betting/sports/filter/football"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Handle cookie banner
            try:
                await page.click("#onetrust-accept-btn-handler", timeout=5000)
                print("Accepted cookies")
            except:
                pass
                
            print("Scanning for league links...")
            # We want links that look like /betting/sports/filter/football/country/league
            # Usually in a side menu or a "Browse" list.
            
            # Explicitly wait for and try to click "Browse Football" or similar if present
            # Kambi often has a "Browse" tab or button.
            # Let's dump the text content of buttons to find a candidate
            
            try:
                # Common Kambi selectors
                await page.wait_for_selector("li[data-id='browse']", timeout=5000)
                await page.click("li[data-id='browse']")
                print("Clicked Browse tab")
                await page.wait_for_timeout(3000)
            except:
                print("Could not find/click Browse tab via data-id")
                
                # Try finding by text "All Football" or "Browse"
                try:
                    await page.click("text=All Football", timeout=3000)
                    print("Clicked 'All Football' text")
                    await page.wait_for_timeout(3000)
                except:
                    pass

            print("Scanning for league links...")
            
            # Dump full HTML for debug if 0 links found again
            # Extract all hrefs
            links = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => a.href);
            }""")
            
            football_links = [l for l in links if '/betting/sports/filter/football/' in l]
            
            unique_leagues = set()
            for l in football_links:
                parts = l.split('/filter/football/')
                if len(parts) > 1:
                    suffix = parts[1]
                    segments = suffix.strip('/').split('/')
                    # Valid league usually: country/league (2 parts)
                    # e.g. england/premier_league
                    if len(segments) >= 2: 
                        unique_leagues.add(l)
            
            print(f"Found {len(unique_leagues)} unique potential league URLs.")
            for ul in sorted(list(unique_leagues))[:20]:
                print(ul)
            
            if len(unique_leagues) == 0:
                print("Debug: No leagues found. Dumping page content length...")
                content = await page.content()
                print(f"Content Length: {len(content)}")
                # Check if we are blocked
                if len(content) < 1000:
                    print("POSSIBLE BLOCK DETECTED")
                else:
                    with open("unibet_leagues_dump.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    print("Saved unibet_leagues_dump.html for inspection")
            
        except Exception as e:
            print(f"Error: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_leagues())
