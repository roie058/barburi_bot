
from bs4 import BeautifulSoup
import os

def parse_links():
    file_path = "unibet_leagues_dump.html"
    if not os.path.exists(file_path):
        print("File not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all('a')
    
    print(f"Found {len(links)} links.")
    
    # Filter for anything football related
    football_links = [l.get('href', '') for l in links if l.get('href')]
    football_links = [l for l in football_links if 'football' in l or 'england' in l or 'premier' in l]
    
    unique_links = sorted(list(set(football_links)))
    
    # Filter for deep links (likely leagues)
    # usually /football/country/league or /football/league
    # e.g. /betting/odds/football/argentina/liga-profesional (depth 5)
    
    league_urls = []
    base_url = "https://www.unibet.co.uk"
    
    for l in unique_links:
        # cleanup
        l = l.split('#')[0]
        if not l.startswith('/'): continue
        
        parts = l.strip('/').split('/')
        if len(parts) >= 4: # betting/odds/football/something
             league_urls.append(base_url + l)

    unique_api_urls = sorted(list(set(league_urls)))
    print(f"Found {len(unique_api_urls)} valid league URLs.")
    
    import json
    with open("data/unibet_leagues.json", "w") as f:
        json.dump(unique_api_urls, f, indent=2)
    print("Saved to data/unibet_leagues.json")

if __name__ == "__main__":
    parse_links()
