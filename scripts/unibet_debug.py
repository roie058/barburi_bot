import asyncio
import json
from playwright.async_api import async_playwright

async def run_visual_test():
    async with async_playwright() as p:
        args = ['--disable-blink-features=AutomationControlled', '--disable-infobars']
        browser = await p.chromium.launch(headless=False, args=args, channel="chrome")
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/London"
        )
        page = await context.new_page()
        
        try:
            url = "https://www.unibet.co.uk/betting/sports/filter/football/england/premier_league"
            await page.goto(url, timeout=30000)
            await asyncio.sleep(5.0)
            
            # Run the exact regex/parser logic from unibet.py
            js_script = r"""() => {
                const selector = '[data-test-name="contestCard"], [data-test-name="match-group-header"], [data-test-name="MainHeaderText"], [data-test-name="MainHeader"], .KambiBC-event-groups-list__header';
                const allNodes = Array.from(document.querySelectorAll(selector));
                
                let nodeLog = [];
                const results = [];
                let currentDate = "Today";
                
                const dateRegex = new RegExp("^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Today|Tomorrow)|([0-9]{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))", "i");

                allNodes.forEach((node, nodeIdx) => {
                    const textContent = node.textContent.replace(/[\n\r]+/g, ' ').trim(); 
                    let isHeader = false;
                    const isCard = node.matches('[data-test-name="contestCard"]');
                    const isHeaderClass = node.matches('[data-test-name="match-group-header"]') ||
                                          node.matches('[data-test-name="MainHeaderText"]') ||
                                          node.matches('[data-test-name="MainHeader"]') ||
                                          node.classList.contains('KambiBC-event-groups-list__header');
                    
                    if (isHeaderClass || (!isCard && textContent.length < 50 && dateRegex.test(textContent))) {
                        isHeader = true;
                    }

                    if (isHeader) {
                        if (dateRegex.test(textContent)) {
                            currentDate = textContent.trim();
                        }
                        return;
                    }

                    if (isCard) {
                        const html = node.innerHTML;
                        const separated = html.replace(/<[^>]+>/g, '|');
                        const parts = separated.split('|').map(p => p.trim()).filter(p => p.length > 0 && p !== '&nbsp;');
                        
                        nodeLog.push({
                            index: nodeIdx,
                            date: currentDate,
                            parts: parts
                        });
                    }
                });
                return {count: results.length, logs: nodeLog};
            }"""
            
            data = await page.evaluate(js_script)
            
            with open("unibet_dom_debug.json", "w") as f:
                json.dump(data, f, indent=4)
                
            print(f"Extraction successful. Got {len(data['logs'])} raw card logs.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_visual_test())
