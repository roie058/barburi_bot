import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="en-GB"
        )
        page = await context.new_page()
        
        # Capture network
        captured_urls = []
        page.on("response", lambda response: captured_urls.append((response.url, response.status, response.headers.get("content-type", ""))))
        
        try:
            # Try a direct deep link to football
            url = "https://www.unibet.co.uk/betting/sports/filter/football"
            print(f"Navigating to {url}...")
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(8000)
            
            title = await page.title()
            content = await page.content()
            
            # Write log
            with open("unibet_research.log", "w", encoding="utf-8") as f:
                f.write(f"Page Title: {title}\n")
                if "Cloudflare" in title or "Access Denied" in content:
                    f.write("BLOCKED: Cloudflare/Access Denied detected.\n")
                else:
                    f.write("Access seems OK.\n")
                
                try:
                    # Wait for specific text to appear to ensure content is loaded
                    print("Waiting for 'Arsenal' or 'Liverpool'...")
                    await page.wait_for_selector("text=Arsenal", timeout=15000)
                    f.write("Found 'Arsenal' via wait_for_selector!\n")
                except:
                    try:
                        await page.wait_for_selector("text=Liverpool", timeout=15000)
                        f.write("Found 'Liverpool' via wait_for_selector!\n")
                    except:
                        f.write("Timeout waiting for teams.\n")

                # Refresh content after wait
                content = await page.content()

                if "Arsenal" in content or "Liverpool" in content:
                    f.write("Teams confirmed in content.\n")
                    
                    # Find all elements with team names to guess class structure
                    # We saw <p data-dn="Text" ...> in previous partial dump.
                    # Let's find all text elements that contain Arsenal
                    elements = await page.locator("text=Arsenal").all()
                    f.write(f"Found {len(elements)} elements with text 'Arsenal'.\n")
                    
                    for i, el in enumerate(elements):
                        # Get parent hierarchy to find the match card
                        parent = el.locator("xpath=./../..") # Go up 2 levels
                        html = await parent.inner_html()
                        f.write(f"\n--- Arsenal Parent {i} HTML ---\n{html[:1000]}\n")
                        
                        # Try to go higher to find the full match row?
                        grandparent = el.locator("xpath=./../../../../..") # Go up 5
                        gp_html = await grandparent.inner_html()
                        f.write(f"\n--- Arsenal Grandparent {i} HTML ---\n{gp_html[:1000]}\n")

                    # Save full content again just in case
                    with open("unibet_page_dump_success.html", "w", encoding="utf-8") as html_f:
                        html_f.write(content)

                else:
                    f.write("Teams NOT found in content even after wait.\n")

                f.write("\n--- Interesting Network Calls ---\n")
                api_calls = [u for u in captured_urls if "json" in u[0] or "kambi" in u[0] or "offermatrix" in u[0]]
                for u, s, t in api_calls: 
                    f.write(f"[{s}] {u} ({t})\n")
                    
        except Exception as e:
            with open("unibet_research.log", "w") as f:
                f.write(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
