
import difflib
import json
import os

class GameWrapper:
    def __init__(self, data):
        self.data = data
        self.game = data.get('game', '')
        self.date = str(data.get('date', ''))
        self.team1 = data.get('team1', '')
        self.team2 = data.get('team2', '')
        self.link = data.get('link', '')
        # Support Hebrew columns if present, fallback to main
        self.team1_hebrew = data.get('team1_hebrew', self.team1)
        self.team2_hebrew = data.get('team2_hebrew', self.team2)
        
    def get_key(self):
        return tuple(sorted([self.team1.lower(), self.team2.lower()]))

def _clean_team_name(name):
    name = str(name).lower()
    suffixes = [
        "town", "city", "united", "rovers", "athletic", "fc", "afc", " wanderers", 
        " county", " hotspur", " albion", " borough", " argyle", " alexandra",
        " metropolitan", " orient", " downs", " sporting"
    ]
    for s in suffixes:
        name = name.replace(s.lower(), "")
    
    # Strip common Arabic prefix 'Al-' or 'Al ' to prevent false positives like Al-Najma vs Al-Nassr
    name = name.replace("al-", "").replace("al ", "")
    
    if "congo" in name: name = "congo dr"
    return name.strip()

def match_datasets(df1, df2):
    """
    Pairs games between two dataframes.
    Returns: (matched_count, matched_pairs_list, unmatched_list_from_df1)
    """
    if df1.empty or df2.empty:
        return 0, [], []
        
    games1 = [GameWrapper(row.to_dict()) for _, row in df1.iterrows()]
    games2 = [GameWrapper(row.to_dict()) for _, row in df2.iterrows()]
    
    # Simple Exact Match by sorted team key
    g2_map = {g.get_key(): g for g in games2}
    
    matched = []
    unmatched1 = []
    
    # Track used g2 games to avoid double matching? 
    # For efficiency we stick to 1-to-1 via key/best-match.
    
    for g1 in games1:
        key = g1.get_key()
        if key in g2_map:
            matched.append((g1, g2_map[key]))
        else:
            # Fuzzy match fallback
            best_score = 0
            best_match = None
            t1_clean = _clean_team_name(g1.team1)
            t2_clean = _clean_team_name(g1.team2)
            
            for g2 in games2:
                # Basic fuzzy check on teams
                target1 = _clean_team_name(g2.team1)
                target2 = _clean_team_name(g2.team2)
                
                # Check 1-1, 2-2
                s1 = difflib.SequenceMatcher(None, t1_clean, target1).ratio()
                s2 = difflib.SequenceMatcher(None, t2_clean, target2).ratio()
                score1 = (s1 + s2)/2
                
                # Check 1-2, 2-1 (swapped)
                s3 = difflib.SequenceMatcher(None, t1_clean, target2).ratio()
                s4 = difflib.SequenceMatcher(None, t2_clean, target1).ratio()
                score2 = (s3 + s4)/2
                
                top_score = max(score1, score2)
                if top_score > best_score:
                    best_score = top_score
                    best_match = g2
            
            if best_score > 0.85: # 85% matching threshold
                matched.append((g1, best_match))
            else:
                unmatched1.append(g1)
                

    return len(matched), matched, unmatched1

def update_unibet_team_map(unibet_df):
    """
    Updates data/unibet_teams_map.json with team names from unibet_df.
    - Keys: Unibet English names
    - Values: Hebrew names from name_mappings.json if found, else empty string.
    """
    if unibet_df is None or unibet_df.empty:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    mappings_path = os.path.join(base_dir, "data", "name_mappings.json")
    unibet_map_path = os.path.join(base_dir, "data", "unibet_teams_map.json")

    # 1. Load existing name_mappings (Hebrew -> English)
    reverse_map = {}
    if os.path.exists(mappings_path):
        try:
            with open(mappings_path, "r", encoding="utf-8") as f:
                name_mappings = json.load(f)
                # Create reverse map: English -> Hebrew
                for heb, eng in name_mappings.items():
                    if eng not in reverse_map:
                        reverse_map[eng] = heb
        except Exception as e:
            print(f"Error loading name_mappings.json: {e}")

    # 2. Load existing unibet_teams_map.json
    unibet_teams_map = {}
    if os.path.exists(unibet_map_path):
        try:
            with open(unibet_map_path, "r", encoding="utf-8") as f:
                unibet_teams_map = json.load(f)
        except Exception as e:
            print(f"Error loading unibet_teams_map.json: {e}")

    # 3. Extract unique team names from unibet_df
    new_teams = set()
    if 'team1' in unibet_df.columns:
        new_teams.update(unibet_df['team1'].unique())
    if 'team2' in unibet_df.columns:
        new_teams.update(unibet_df['team2'].unique())

    # 4. Map new teams
    changed = False
    for team in new_teams:
        if team not in unibet_teams_map:
            # Try to find in reverse_map
            hebrew_name = reverse_map.get(team, "")
            unibet_teams_map[team] = hebrew_name
            changed = True

    # 5. Save if changed
    if changed:
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(unibet_map_path), exist_ok=True)
            with open(unibet_map_path, "w", encoding="utf-8") as f:
                json.dump(unibet_teams_map, f, ensure_ascii=False, indent=4)
            print(f"Updated {unibet_map_path} with new Unibet team names.")
        except Exception as e:
            print(f"Error saving unibet_teams_map.json: {e}")
