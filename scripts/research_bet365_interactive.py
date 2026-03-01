import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        # Add args to reduce bot detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-GB"
        )
        page = await context.new_page()
        
        try:
            url = "https://www.bet365.com/"
            print(f"Navigating to {url}...")
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Identify 'Soccer' or 'Football' button
            # Usually Bet365 has a side menu or top menu
            # We dump the text to find the exact label
            text = await page.inner_text("body")
            if "Soccer" in text:
                print("Found 'Soccer' text. Attempting to click...")
                # Try to click text=Soccer
                try:
                    await page.get_by_text("Soccer", exact=True).first.click()
                except:
                    # Try finding it in a list of sports
                    all_text = await page.locator("body").all_inner_texts()
                    # Just generic "click" on the word might fail if it's not the interactive element.
                    pass
            
            await page.wait_for_timeout(5000)
            
            # Check for generic "United Kingdom" or "Premier League"
            content = await page.content()
            if "Man City" in content or "Arsenal" in content:
                print("SUCCESS: Found teams!")
            else:
                print("STILL FAILING: Teams not found.")
                
            # Log frames to see if headers are present
            # page.frames might reveal if odds are in an iframe (unlikely for modern SPA but possible)
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
