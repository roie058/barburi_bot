import pandas as pd
from typing import List, Dict
import difflib
from datetime import datetime

class Game:
    def __init__(self, data: Dict):
        self.game = data.get('game', '')
        self.date_raw = data.get('date', '')
        self.num_1 = float(data.get('num_1', 0))
        self.num_X = float(data.get('num_X', 0))
        self.num_2 = float(data.get('num_2', 0))
        self.link = data.get('link', '')
        self.source = data.get('source', '')
        
        # Normalize teams
        if ' - ' in self.game:
            parts = self.game.split(' - ')
            self.team1 = parts[0].strip()
            self.team2 = parts[1].strip()
        else:
            self.team1 = self.game
            self.team2 = ""
            
        # Standardize date to YYYY-MM-DD
        self.date = self._normalize_date(str(self.date_raw))

    def _normalize_date(self, d):
        try:
            # Winner format: 251226 (YYMMDD)
            if len(d) == 6 and d.isdigit():
                return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
            # Pinnacle format: 2025-12-26T20:00:00Z
            if 'T' in d:
                return d.split('T')[0]
            return d
        except:
            return d
            
    def get_key(self):
        return tuple(sorted([self.team1.lower(), self.team2.lower()]))

def check_favorite_flip(local: Game, remote: Game):
    # Determine favorites
    local_fav = 0
    if local.num_1 < local.num_2:
        local_fav = 1
    elif local.num_2 < local.num_1:
        local_fav = 2
    
    remote_fav = 0
    if remote.num_1 < remote.num_2:
        remote_fav = 1
    elif remote.num_2 < remote.num_1:
        remote_fav = 2
        
    if local_fav != 0 and remote_fav != 0 and local_fav != remote_fav:
        # Check Winner Confidence Gap
        WINNER_CONFIDENCE_THRESHOLD = 0.75
        
        winner_internal_gap = abs(local.num_1 - local.num_2)
        if winner_internal_gap < WINNER_CONFIDENCE_THRESHOLD:
            return None
            
        gap_1 = abs(local.num_1 - remote.num_1)
        gap_2 = abs(local.num_2 - remote.num_2)
        total_gap = gap_1 + gap_2
        
        # Format Date for display: YYYY-MM-DD -> DD-MM-YYYY
        d_parts = local.date.split('-')
        formatted_date = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}" if len(d_parts) == 3 else local.date
        
        winner_fav_name = local.team1 if local_fav == 1 else local.team2
        pinnacle_fav_name = local.team1 if remote_fav == 1 else local.team2
        
        return {
            "type": "favorite_flip",
            "game": local.game,
            "date": formatted_date,
            "gap": round(total_gap, 2),
            "winner_fav": winner_fav_name,
            "pinnacle_fav": pinnacle_fav_name,
            "winner_odds": {"1": local.num_1, "X": local.num_X, "2": local.num_2},
            "pinnacle_odds": {"1": remote.num_1, "X": remote.num_X, "2": remote.num_2}
        }
    return None

def _clean_team_name(name: str) -> str:
    """Removes common suffixes to improve matching."""
    name = name.lower()
    suffixes = [
        "town", "city", "united", "rovers", "athletic", "fc", "afc", " wanderers", 
        " county", " hotspur", " albion", " borough", " argyle", " alexandra",
        " metropolitan", " orient", " downs", " sporting"
    ]
    for s in suffixes:
        name = name.replace(s.lower(), "")
    
    # Handle "DR Congo" / "Congo DR"
    if "congo" in name:
        name = "congo dr"
        
    return name.strip()

def compare_games(winner_df: pd.DataFrame, pinnacle_df: pd.DataFrame):
    winner_games = [Game(row.to_dict()) for index, row in winner_df.iterrows()]
    pinnacle_games = [Game(row.to_dict()) for index, row in pinnacle_df.iterrows()]
    
    # Index Pinnacle games by date
    p_by_date = {}
    for g in pinnacle_games:
        if g.date not in p_by_date: p_by_date[g.date] = []
        p_by_date[g.date].append(g)
        
    opportunities = []
    matched_count = 0
    
    for w_game in winner_games:
        # Check Winner's date AND +/- 1 day to account for timezone shifts
        w_dt = None
        target_dates = [w_game.date]
        try:
            w_dt = datetime.strptime(w_game.date, "%Y-%m-%d")
            from datetime import timedelta
            prev_day = (w_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            next_day = (w_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            target_dates.extend([prev_day, next_day])
        except:
            pass
            
        potential_pinnacle = []
        for d in target_dates:
            potential_pinnacle.extend(p_by_date.get(d, []))

        if not potential_pinnacle:
            continue
            
        best_match = None
        exact_match = None
        
        # 1. Look for exact match
        w_key = w_game.get_key()
        for p_game in potential_pinnacle:
            if w_key == p_game.get_key():
                exact_match = p_game
                break
        
        if exact_match:
            best_match = exact_match
        else:
            # 2. Try Fuzzy Match team-by-team with normalized names
            max_overall_score = 0
            
            w1_clean = _clean_team_name(w_game.team1)
            w2_clean = _clean_team_name(w_game.team2)
            
            for p_game in potential_pinnacle:
                p1_clean = _clean_team_name(p_game.team1)
                p2_clean = _clean_team_name(p_game.team2)
                
                # Calculate similarity for both orientations
                s1 = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
                s2 = difflib.SequenceMatcher(None, w2_clean, p2_clean).ratio()
                score_straight = (s1 + s2) / 2
                
                s3 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
                s4 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
                score_swapped = (s3 + s4) / 2
                
                best_score = max(score_straight, score_swapped)
                
                # Using 0.65 as a safe cutoff for normalized name comparison
                if best_score > 0.65 and best_score > max_overall_score:
                    max_overall_score = best_score
                    best_match = p_game
                    
        if best_match:
            matched_count += 1
            
            # Determine if we need to swap Pinnacle's odds to match Winner's orientation
            # We compare the cleaned names used for matching
            w1_clean = _clean_team_name(w_game.team1)
            p1_clean = _clean_team_name(best_match.team1)
            
            # Check similarity of Winner Team 1 vs Pinnacle Team 1
            s_straight = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
            
            # Check similarity of Winner Team 1 vs Pinnacle Team 2
            p2_clean = _clean_team_name(best_match.team2)
            s_swapped = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
            
            final_p_odds = {
                "num_1": best_match.num_1,
                "num_X": best_match.num_X,
                "num_2": best_match.num_2
            }
            
            if s_swapped > s_straight:
                # Team order is reversed on Pinnacle (Winner: A-B, Pinnacle: B-A)
                # Swap Pinnacle's 1 and 2 odds to align with Winner's Team 1 and Team 2
                final_p_odds["num_1"] = best_match.num_2
                final_p_odds["num_2"] = best_match.num_1
                
            # Create a virtual aligned Game for check_favorite_flip
            aligned_p_game = Game({
                "game": f"{w_game.team1} - {w_game.team2}",
                "date": best_match.date,
                "num_1": final_p_odds["num_1"],
                "num_X": final_p_odds["num_X"],
                "num_2": final_p_odds["num_2"],
                "link": best_match.link
            })
            
            res = check_favorite_flip(w_game, aligned_p_game)
            if res:
                opportunities.append(res)
    
    return opportunities, matched_count
