
import difflib

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
