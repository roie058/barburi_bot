
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
from scrapers.stealth_config import (
    STEALTH_ARGS, get_context_options, apply_stealth,
    human_delay
)

class UnibetScraper:
    def __init__(self, headless=False):
        # Default to headless=False as Unibet blocks headless/API often.
        self.headless = headless
        self.base_url = "https://www.unibet.co.uk"

    def _parse_date(self, d_str):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        try:
            parsed_date = None
            if d_str == "Today":
                parsed_date = today
            else:
                # Clean string
                clean_d = d_str.strip()
                
                # Remove weekdays
                weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                for w in weekdays:
                    clean_d = clean_d.replace(w, "").strip()
                    
                # Try standard formats
                formats = [
                    "%d %b %H:%M", # 01 Jan 15:00
                    "%d %B %H:%M", # 01 January 15:00
                    "%d %b %Y",    # 01 Jan 2026 (New Unibet Header)
                    "%d %B %Y",    # 01 January 2026
                    "%d %b",       # 01 Jan
                    "%d %B"        # 01 January
                ]
                
                for fmt in formats:
                    try:
                        dt_part = datetime.strptime(clean_d, fmt)
                        
                        # If format has year, use it
                        if "%Y" in fmt:
                             parsed_date = dt_part
                        else:
                            parsed_date = dt_part.replace(year=today.year)
                            if parsed_date.month < today.month:
                                parsed_date = parsed_date.replace(year=today.year + 1)
                        break
                    except: continue
                        
                if not parsed_date:
                    # "01/01 15:00"
                    if "/" in clean_d and len(clean_d.split("/")) >= 2:
                        try:
                            dt_part = datetime.strptime(clean_d, "%d/%m %H:%M")
                            parsed_date = dt_part.replace(year=today.year)
                            if parsed_date.month < today.month:
                                parsed_date = parsed_date.replace(year=today.year + 1)
                        except: pass
                            
                    # "Tomorrow 15:00"
                    elif "tomorrow" in clean_d.lower():
                        parsed_date = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                        try:
                            if len(clean_d.split()) > 1:
                                t_str = clean_d.split()[-1]
                                if ":" in t_str:
                                    t_part = datetime.strptime(t_str, "%H:%M")
                                    parsed_date = parsed_date.replace(hour=t_part.hour, minute=t_part.minute)
                        except: pass
                        
                    # "Today 15:00"
                    elif "today" in clean_d.lower():
                        parsed_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                        try:
                            if len(clean_d.split()) > 1:
                                t_str = clean_d.split()[-1]
                                if ":" in t_str:
                                    t_part = datetime.strptime(t_str, "%H:%M")
                                    parsed_date = parsed_date.replace(hour=t_part.hour, minute=t_part.minute)
                        except: pass
                        
                    # "15:00" (Today implied)
                    elif len(clean_d) == 5 and ":" in clean_d:
                        try:
                            parsed_date = datetime.strptime(clean_d, "%H:%M").replace(year=today.year, month=today.month, day=today.day)
                        except: pass

            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d %H:%M")
            return d_str
            
        except:
            return d_str
        
    async def get_odds(self, leagues=None):
        async with async_playwright() as p:
            # Launch with stealth args
            browser = await p.chromium.launch(
                headless=self.headless,
                args=STEALTH_ARGS,
                channel="chrome"
            )
            
            context = await browser.new_context(**get_context_options())
            
            # Load leagues
            target_params = []
            if leagues is not None:
                target_params = leagues
                if not target_params: 
                    print("UnibetScraper: Scrape list is empty, skipping scrape.")
            else:
                json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'unibet_leagues.json')
                
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        full_urls = json.load(f)
                        for u in full_urls:
                            if "/betting/odds/" in u:
                                param = u.split("/betting/odds/")[1]
                                # SAFETY FILTER: Skip match URLs and outrights to prevent 0-match hangs
                                if "-vs-" in param or "/outrights" in param or "player-specials" in param:
                                    continue
                                target_params.append(param)
                
                if not target_params:
                    target_params = ["football/england/premier_league"]
                
            print(f"Starting Concurrent DOM Scrape for {len(target_params)} leagues...")
            
            all_matches = []
            
            # Reduced semaphore from 4 to 3 to look less aggressive
            sem = asyncio.Semaphore(4)

            # Define the actual scraping logic as a local async function (captured self)
            async def _scrape_logic(context, param):
                page = None
                league_matches = []
                try:
                    # Page instantiation protected
                    page = await context.new_page()
                    await apply_stealth(page)
                    url = f"https://www.unibet.co.uk/betting/sports/filter/{param}"

                    # Retry logic
                    for attempt in range(3):
                        try:
                            if attempt > 0:
                                # Randomized retry delay
                                await human_delay(2500 + attempt * 1000, 800)

                            await page.goto(url, timeout=60000)
                            try:
                                await page.wait_for_load_state("networkidle", timeout=5000)
                            except: pass

                            # Handle cookie banner
                            try:
                                await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
                                await page.click("#onetrust-accept-btn-handler")
                                await human_delay(1800, 500)
                            except: pass

                            # Wait for hydration (CRITICAL: matches debug script)
                            await human_delay(4500, 1500)

                            # Scroll logic for THIS tab (Dynamic Deep Scroll)
                            prev_height = 0
                            no_change_count = 0
                            
                            MAX_SCROLLS = random.randint(12, 18)  # Reduced from 35-45 for efficiency
                            
                            for _ in range(MAX_SCROLLS): 
                                # 1. Scroll random amount
                                scroll_amount = random.randint(400, 800)
                                await page.evaluate(f"window.scrollBy(0, {scroll_amount})") 
                                await human_delay(450, 200)
                                
                                # 2. Try to Expand Headers in Viewport (Iterative)
                                try:
                                    await page.evaluate("""() => {
                                        const dateHeaders = document.querySelectorAll('[data-test-name="MainHeader"], [data-test-name="match-group-header"]');
                                        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
                                        buttons.forEach(b => {
                                             if (b.innerText.toLowerCase().includes("show more")) b.click();
                                        });
                                    }""")
                                except: pass
                                
                                await human_delay(450, 200)

                            # Fast DOM extraction via JS evaluation
                            try:
                                js_script = r"""() => {
                                    const selector = '[data-test-name="contestCard"], [data-test-name="match-group-header"], [data-test-name="MainHeaderText"], [data-test-name="MainHeader"], .KambiBC-event-groups-list__header';
                                    const allNodes = Array.from(document.querySelectorAll(selector));
                                    
                                    let nodeLog = [];
                                    const results = [];
                                    let currentDate = "Today";
                                    
                                    const dateRegex = new RegExp("^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Today|Tomorrow)|([0-9]{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))", "i");

                                    allNodes.forEach((node, nodeIdx) => {
                                        try {
                                            const textContent = node.textContent.replace(/[\n\r]+/g, ' ').trim(); 
                                            
                                            let isHeader = false;
                                            const isCard = node.matches('[data-test-name="contestCard"]');
                                            
                                            const isHeaderClass = node.matches('[data-test-name="match-group-header"]') ||
                                                                  node.matches('[data-test-name="MainHeaderText"]') ||
                                                                  node.matches('[data-test-name="MainHeader"]') ||
                                                                  node.classList.contains('KambiBC-event-groups-list__header');
                                            
                                            if (isHeaderClass) {
                                                isHeader = true;
                                            } else if (!isCard) {
                                                isHeader = true;
                                            }
                                            
                                            if (textContent.length < 50 && dateRegex.test(textContent)) {
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
                                                
                                                const isOdd = (s) => ( /^[0-9]+\/[0-9]+$/.test(s) ) || ( /^[0-9]+(\.[0-9]+)?$/.test(s) && parseFloat(s) > 1.0 && s.length < 8 );
                                                
                                                const oddsIndices = [];
                                                parts.forEach((p, i) => { if(isOdd(p)) oddsIndices.push(i); });
                                                
                                                if (oddsIndices.length >= 3) {
                                                    const o1_idx = oddsIndices[0];
                                                    const ox_idx = oddsIndices[1];
                                                    const o2_idx = oddsIndices[2];
                                                    
                                                    const parseOdd = (s) => {
                                                        if (s.includes('/')) {
                                                            const [n, d] = s.split('/').map(Number);
                                                            return 1 + (n/d);
                                                        }
                                                        return parseFloat(s);
                                                    };
                                                    
                                                    const o1 = parseOdd(parts[o1_idx]);
                                                    const ox = parseOdd(parts[ox_idx]);
                                                    const o2 = parseOdd(parts[o2_idx]);
                                                    
                                                    const preOdds = parts.slice(0, o1_idx);
                                                    
                                                    const candidates = preOdds.filter(c => 
                                                        !c.match(/^[0-9]+$/) &&
                                                        c !== "Live" && c !== "Cash Out" && c !== "Streaming" && c !== "Watch"
                                                    );
                                                    
                                                    let time = "";
                                                    const timeIdx = candidates.findIndex(c => /^[0-9]{2}:[0-9]{2}$/.test(c));
                                                    if (timeIdx !== -1) {
                                                        time = candidates[timeIdx];
                                                        candidates.splice(timeIdx, 1);
                                                    }
                                                    
                                                    let t1 = "", t2 = "";
                                                    if (candidates.length >= 2) {
                                                        t1 = candidates[candidates.length-2];
                                                        t2 = candidates[candidates.length-1];
                                                    } else if (candidates.length === 1) {
                                                        if (candidates[0].includes(' - ')) {
                                                            [t1, t2] = candidates[0].split(' - ');
                                                        } else {
                                                            t1 = candidates[0];
                                                        }
                                                    }
                                                    
                                                    let finalDate = currentDate;
                                                    if (time) finalDate = finalDate + " " + time;
                                                    
                                                    if (t1 && t2) {
                                                        results.push({
                                                            "game": `${t1} - ${t2}`,
                                                            "date": finalDate,
                                                            "num_1": o1, "num_X": ox, "num_2": o2,
                                                            "team1": t1, "team2": t2,
                                                            "raw_header": currentDate
                                                        });
                                                    }
                                                }
                                            }
                                        } catch(err) {}
                                    });
                                    return { results, nodeLog }; 
                                }"""
                                matches = await page.evaluate(js_script)
                            except Exception as e:
                                pass
                                matches = []
                                
                            if isinstance(matches, dict):
                                matches = matches.get('results', [])
                                
                            # --- FALLBACK SCRAPER ---
                            if not matches:
                                matches = await page.evaluate(r"""() => {
                                    const results = [];
                                    const lines = document.body.innerText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
                                    let currentDate = "Today";
                                    const dateRegex = /^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+[0-9]{1,2}(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*/i;
                                    
                                    for(let i=0; i<lines.length; i++) {
                                        const text = lines[i];
                                        if (text.match(dateRegex)) { currentDate = text; continue; }
                                        if (text === "Today" || text === "Tomorrow") { currentDate = text; continue; }
                                        
                                        if (text.includes(" vs ")) {
                                            const parts = text.split(" vs ");
                                            if (parts.length === 2 && parts[0].length > 2 && parts[1].length > 2) {
                                                const t1 = parts[0].trim();
                                                const t2 = parts[1].trim();
                                                let oddsFound = [];
                                                for(let j=1; j<20; j++) {
                                                    if (i+j >= lines.length) break;
                                                    const nextLine = lines[i+j];
                                                    if (/^[0-9]+(\.[0-9]+)?$/.test(nextLine)) {
                                                        const val = parseFloat(nextLine);
                                                        if (val > 1.0 && val < 100.0 && !oddsFound.includes(val)) oddsFound.push(val);
                                                    }
                                                    if ((nextLine.includes(" vs ") && j > 1) || nextLine.match(dateRegex)) break; 
                                                }
                                                if (oddsFound.length >= 3) {
                                                    results.push({
                                                        "game": `${t1} - ${t2}`,
                                                        "date": currentDate,
                                                        "num_1": oddsFound[0], "num_X": oddsFound[1], "num_2": oddsFound[2],
                                                        "team1": t1, "team2": t2, "raw_header": currentDate, "source": "Unibet_Fallback_Text"
                                                    });
                                                }
                                            }
                                        }
                                    }
                                    return results;
                                }""")
                            
                            if matches:
                                for m in matches:
                                    m['link'] = url
                                    m['source'] = 'Unibet'
                                league_matches = matches
                                break # Success
                            
                            # Retry if empty league (no error title)
                            if not matches and attempt < 2:
                                title = await page.title()
                                if not any(x in title for x in ["503", "Unavailable", "Just a moment", "Challenge", "Error"]):
                                    try:
                                        content = await page.content()
                                        with open(f"unibet_failed_{attempt}.html", "w", encoding="utf-8") as f:
                                            f.write(content)
                                    except: pass
                                    continue
                                
                                break
                                
                        except Exception as e:
                            # Catch playwright timeout or other errors, but don't dump the full stacktrace
                            err_str = str(e)
                            if "Timeout" not in err_str:
                                print(f"Warning: Issue parsing Unibet DOM ({err_str[:80]}...)")
                            pass
                    
                    if page:
                        await page.close()
                    return league_matches

                except Exception as e:
                    if page: 
                        try: await page.close()
                        except: pass
                    return []

            
            # Wrapper with timeout and error handling for parallel execution
            async def scrape_league(param):
                async with sem:
                    try:
                        # Add random stagger between tasks starting
                        await asyncio.sleep(random.uniform(0.3, 1.5))
                        print(f"Scraping Unibet: {param}", flush=True)
                        return await asyncio.wait_for(_scrape_logic(context, param), timeout=120.0)
                    except asyncio.TimeoutError:
                        print(f"Timeout: {param}", flush=True)
                        return []
                    except Exception as e:
                        return []
            
            tasks = [scrape_league(p) for p in target_params]
            try:
                results = await asyncio.gather(*tasks)
                
                for r in results:
                    all_matches.extend(r)
            finally:
                await browser.close()
            
            # Post-processing: Parse dates
            for m in all_matches:
                m['date'] = self._parse_date(m['date'])

            print(f"Concurrent DOM Scrape Finished. Found {len(all_matches)} matches.", flush=True)
            
            return pd.DataFrame(all_matches)

if __name__ == "__main__":
    scraper = UnibetScraper(headless=True)
    print("Running Debug Test for Premier League with Retry Logic...")
    df = asyncio.run(scraper.get_odds(leagues=["football/england/premier_league"]))
    if not df.empty:
        pd.set_option('display.max_rows', None)
        print(df[['game', 'date', 'num_1']].to_string())
    else:
        print("Empty DataFrame - No matches found.")
