import sys
import os
sys.path.append(os.getcwd())
from scrapers.unibet import UnibetScraper
from playwright.sync_api import sync_playwright
import time

def debug_league(league_url_suffix, target_team):
    print(f"--- Debugging {league_url_suffix} looking for '{target_team}' ---")
    with sync_playwright() as p:
        # Launch visible to capture screenshot if needed, but headless is fine for text check
        browser = p.chromium.launch(headless=True) 
        scraper = UnibetScraper(headless=True)
        # We need to manually inject the browser/page into the scraper or just use the scraper's internal logic methods if possible.
        # UnibetScraper structure assumes headers/setup. 
        # Better to just reuse its _scrape_logic if possible, or replicate the navigation.
        
        # Actually, UnibetScraper.scrape() does the loop.
        # Let's instantiate and call scrape() but ONLY for this league.
        
        # Mocking the league list
        scraper.leagues = [(league_url_suffix, "Debug League")]
        
        # We need to run it. But scrape() runs ALL leagues passed to it.
        # We also want to probe the page state BEFORE scraping result is returned.
        
        # Let's use the scraper's internal driver for fine control
        context = browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        url = f"https://www.unibet.com/betting/sports/filter/{league_url_suffix}"
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        
        # Wait for meaningful load
        try:
             page.wait_for_selector('[data-test-name="contestCard"]', timeout=20000)
             print("Contest cards visible.")
        except:
             print("Timeout waiting for contest cards.")

        # Scroll to bottom to trigger lazy load (Deep Scroll)
        for i in range(10):
             page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
             time.sleep(1.5)
        
        # Check raw text
        content = page.content()
        if target_team in content:
            print(f"SUCCESS: '{target_team}' found in page HTML.")
        else:
            print(f"FAILURE: '{target_team}' NOT found in page HTML.")

        # Now try to parse using the scraper's logic (copy-paste snippet or import if easy)
        # We will count elements
        cards = page.locator('[data-test-name="contestCard"]').all()
        print(f"Found {len(cards)} contest cards via Selector.")
        
        # Check if our specific game is in those cards
        found_in_cards = False
        for i, card in enumerate(cards):
            txt = card.inner_text()
            if target_team in txt:
                # Print clean ASCII to avoid charset issues in console
                clean_txt = txt.encode('ascii', errors='ignore').decode()
                print(f"  -> Found '{target_team}' in Card #{i}: {clean_txt.splitlines()[0:3]}")
                found_in_cards = True
                
        if not found_in_cards:
            print(f"  -> '{target_team}' NOT found in any Card element (Logic Miss).")

        browser.close()

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Debug Everton in Premier League ONLY
    debug_league("football/england/premier-league", "Everton")
