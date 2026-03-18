import asyncio
from playwright.async_api import async_playwright
import os
import sys

# Add parent directory to path so we can import from scrapers
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scrapers.stealth_config import STEALTH_ARGS, get_context_options, apply_stealth, human_delay

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=STEALTH_ARGS, channel="chrome")
        context = await browser.new_context(**get_context_options())
        page = await context.new_page()
        
        # Log browser console to see if our stealth script crashes React
        page.on("console", lambda msg: print(f"Browser Console ({msg.type}): {msg.text}"))
        
        await apply_stealth(page)

        print("Navigating to Unibet...")
        url = "https://www.unibet.co.uk/betting/sports/filter/football"
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as e:
            print(f"Goto error/timeout: {e}")

        # Handle cookie banner just in case
        try:
            await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
            await page.click("#onetrust-accept-btn-handler")
        except: pass
        
        await human_delay(4000, 1000)
        # Probe DOM for data-test-name
        probe = await page.evaluate("""() => {
            const allElements = Array.from(document.querySelectorAll('[data-test-name]'));
            const results = {};
            allElements.forEach(el => {
                try {
                    const name = el.getAttribute('data-test-name');
                    if (!results[name]) {
                        let txt = (el.innerText || '');
                        results[name] = { count: 0, text: txt.substring(0, 50) };
                    }
                    results[name].count += 1;
                } catch(err) { }
            });
            return results;
        }""")
        
        import json
        with open('probe.json', 'w', encoding='utf-8') as f:
            json.dump(probe, f, indent=2)
        print("Wrote probe.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
