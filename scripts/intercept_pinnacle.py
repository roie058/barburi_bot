import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        async def handle_response(response):
            if "api" in response.url or ".json" in response.url:
                print(f"URL: {response.url}")
        
        page.on("response", handle_response)
        await page.goto("https://www.pinnacle.com/en/soccer/matchups/", timeout=60000)
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
