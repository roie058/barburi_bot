import json

with open('pinnacle_alldata_debug.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)

for lid, content in all_data.items():
    matchups_data = content.get("matchups", [])
    markets_data = content.get("markets", [])
    
    # print lengths
    print(f"League {lid}: matchups={len(matchups_data) if isinstance(matchups_data, list) else len(matchups_data.get('matchups', []))}, markets={len(markets_data) if isinstance(markets_data, list) else len(markets_data.get('markets', []))}")
    
    g_list = []
    if isinstance(matchups_data, list): g_list = matchups_data
    elif isinstance(matchups_data, dict):
         if "matchups" in matchups_data: g_list = matchups_data["matchups"]
         elif "leagues" in matchups_data: 
             for l in matchups_data["leagues"]:
                 if "matchups" in l: g_list.extend(l["matchups"])

    m_list = []
    if isinstance(markets_data, list):
        m_list = markets_data
    elif isinstance(markets_data, dict):
         if "leagues" in markets_data:
             for l in markets_data["leagues"]:
                 if "matchups" in l: m_list.extend(l["matchups"])
         elif "matchups" in markets_data:
             m_list = markets_data["matchups"]
    
    odds_map = {}
    for m in m_list:
        m_id = m.get("id") or m.get("matchupId")
        if m_id:
            if m_id not in odds_map: odds_map[m_id] = []
            odds_map[m_id].append(m)

    valid_matches = 0
    for game in g_list:
        if game.get("type", "") == "special": continue 
        if "participants" not in game: continue
        g_id = game.get("id")
        game_markets = odds_map.get(g_id, [])
        if game_markets: valid_matches += 1

    if valid_matches > 0:
        print(f"League {lid} has {valid_matches} valid matches with odds out of {len(g_list)} total games.")
