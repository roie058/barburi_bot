import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd

class PinnacleScraper:
    def __init__(self, headless=True):
        self.headless = headless

    def extract_matches(self, html_content, league_url):
        soup = BeautifulSoup(html_content, "html.parser")
        matches = []
        info_labels = soup.find_all(class_=lambda c: c and 'gameInfoLabel' in c)
        
        processed_rows = set()
        for label in info_labels:
            curr = label
            row = None
            for _ in range(10):
                curr = curr.parent
                if curr is None or curr.name == 'body':
                    break
                buttons = curr.find_all('button')
                if len(buttons) >= 3:
                    row = curr
                    break
                    
            if row and id(row) not in processed_rows:
                processed_rows.add(id(row))
                
                team_labels = row.find_all(class_=lambda c: c and 'gameInfoLabel' in c)
                team_texts = [t.text.replace('(Match)', '').strip() for t in team_labels if t.text.strip()]
                
                if len(team_texts) >= 2:
                    unique_teams = []
                    for t in team_texts:
                        if t not in unique_teams and t.lower() != 'draw':
                            unique_teams.append(t)
                    
                    if len(unique_teams) >= 2:
                        team1 = unique_teams[0]
                        team2 = unique_teams[1]
                        
                        buttons = row.find_all('button')
                        odds = []
                        for b in buttons[:3]:
                            odds.append(b.text.strip())
                            
                        # Basic validation for odds format (numbers with decimals)
                        if len(odds) == 3 and all('.' in o or o.isdigit() for o in odds):
                            try:
                                date_elem = row.find(class_=lambda c: c and 'matchupDate' in c)
                                date_text = date_elem.text.strip() if date_elem else ""
                                
                                matches.append({
                                    "game": f"{team1} - {team2}",
                                    "date": date_text,
                                    "num_1": float(odds[0]),
                                    "num_X": float(odds[1]),
                                    "num_2": float(odds[2]),
                                    "link": league_url
                                })
                            except ValueError:
                                pass # Not valid numbers
        return matches

    async def fetch_league_page(self, context, league_name):
        slug = league_name.lower().replace(" - ", "-").replace(" ", "-")
        url = f"https://www.pinnacle.com/en/soccer/{slug}/matchups/"
        
        page = await context.new_page()
        matches = []
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000) # Give it time to render React
            html = await page.content()
            matches = self.extract_matches(html, url)
        except Exception as e:
            # Simple timeout or navigation error, ignore to continue batching
            pass
        finally:
            await page.close()
            
        return matches

    async def get_odds(self, leagues=None):
        async with async_playwright() as p:
            print(f"Launching browser (headless={self.headless})...")
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
            )
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # 1. Discover All Leagues using API intercept
                leagues_url = "https://www.pinnacle.com/en/soccer/leagues"
                print(f"Navigating to {leagues_url} to discover leagues...")
                
                captured_leagues = []
                async def handle_leagues(response):
                    if "sports/29/leagues" in response.url:
                        try:
                            data = await response.json()
                            if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                                captured_leagues.extend(data)
                        except:
                            pass

                page.on("response", handle_leagues)
                await page.goto(leagues_url, timeout=60000)
                await page.wait_for_timeout(7000) 

                unique_leagues = {l['id']: l for l in captured_leagues if l.get('matchupCount', 0) > 0}
                
                # Filter by provided leagues if argument exists
                target_league_objects = []
                if leagues is not None:
                    if not leagues:
                        print("PinnacleScraper: Scrape list is empty, skipping scrape.")
                        return pd.DataFrame()
                        
                    for l_obj in unique_leagues.values():
                        if l_obj['name'] in leagues:
                            target_league_objects.append(l_obj)
                            
                    print(f"Found {len(unique_leagues)} active leagues. Filtered down to {len(target_league_objects)} target leagues. Fetching DOMs...")
                else:
                    target_league_objects = list(unique_leagues.values())
                    print(f"Found {len(unique_leagues)} active leagues. Fetching DOMs for all...")
                
                # We sort leagues by matchupCount to prioritize big leagues if we hit limits
                sorted_leagues = sorted(target_league_objects, key=lambda x: x.get('matchupCount', 0), reverse=True)
                
                all_matches = []
                chunk_size = 5 # Parallel tabs
                
                for i in range(0, len(sorted_leagues), chunk_size):
                    chunk = sorted_leagues[i:i+chunk_size]
                    print(f"Processing chunk {i // chunk_size + 1}/{len(sorted_leagues) // chunk_size + 1}...")
                    
                    tasks = [self.fetch_league_page(context, l['name']) for l in chunk]
                    results = await asyncio.gather(*tasks)
                    
                    for row_matches in results:
                        all_matches.extend(row_matches)
                        
                    # Small sleep between batches to avoid IP ban
                    await asyncio.sleep(1)

                print(f"Successfully extracted {len(all_matches)} matches via DOM.")
                
                df = pd.DataFrame(all_matches)
                if not df.empty:
                    # Drop duplicates just in case
                    df = df.drop_duplicates(subset=['game'])
                    df.to_csv("pinnacle_all_matches.csv", index=False)
                return df

            except Exception as e:
                print(f"Error scraping Pinnacle: {e}")
                return pd.DataFrame()
            finally:
                await browser.close()

if __name__ == "__main__":
    scraper = PinnacleScraper(headless=True)
    results = asyncio.run(scraper.get_odds())
    print(results.head() if not results.empty else "No results")
