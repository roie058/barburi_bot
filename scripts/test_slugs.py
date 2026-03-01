import urllib.request

slugs = [
    'england-premier-league',
    'england---premier-league',
    'england-premier-league-1980',
    'england_premier_league'
]

for s in slugs:
    try:
        req = urllib.request.Request(f'https://www.pinnacle.com/en/soccer/leagues/{s}/matchups', headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req)
        print(f"{s}: {resp.getcode()}")
    except Exception as e:
        print(f"{s}: Error -> {e}")
