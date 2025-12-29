import asyncio
from playwright.async_api import async_playwright

async def debug_dump():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Stealth
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        try:
            print("Navigating...")
            await page.goto("https://www.pinnacle.com/en/soccer/leagues/", timeout=60000)
            print("Waiting for load...")
            await asyncio.sleep(10)
            
            print("Saving screenshot...")
            await page.screenshot(path="debug.png")
            
            print("Saving HTML...")
            content = await page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dump())
