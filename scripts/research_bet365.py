import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        
        # Capture WebSockets
        page.on("websocket", lambda ws: print(f"WebSocket opened: {ws.url}"))
        page.on("websocketframe", lambda frame: print(f"WS Frame ({len(frame.payload)} bytes)"))
        
        try:
            url = "https://www.bet365.com/#/AC/B1/C1/D13/E40/F4/" 
            print(f"Navigating to {url}...")
            await page.goto(url, timeout=30000)
            
            # Wait for meaningful content
            try:
                # Wait for a class that usually indicates odds. Bet365 classes change, but often contain 'Participant' or 'Odds'
                # Let's just wait a bit longer and dump the body text
                await page.wait_for_timeout(10000)
            except:
                pass
                
            title = await page.title()
            print(f"Page Title: {title}")
            
            # content inspection
            content = await page.content()
            
            # Look for typical odds structure in DOM (e.g. 1.25, 2.00)
            # Or team names like "Man City"
            if "Man City" in content or "Arsenal" in content or "Liverpool" in content:
                print("Found Premier League teams in DOM!")
            else:
                print("Could not find common PL teams in DOM.")
                
            # Print first 500 chars of body text to see if it's empty or loading
            body_text = await page.inner_text("body")
            print(f"Body Text Preview: {body_text[:500]}...")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
