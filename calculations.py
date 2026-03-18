import pandas as pd
from typing import List, Dict
import difflib
import json
import os
from datetime import datetime

# Load mappings
MAPPINGS = {}
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "name_mappings.json")
    with open(path, "r", encoding="utf-8") as f:
        MAPPINGS = json.load(f)
    print(f"Loaded {len(MAPPINGS)} mappings from {path}")
except Exception as e:
    print(f"Error loading name_mappings.json in calculations.py: {e}")
    # fallback to relative
    try:
        with open("data/name_mappings.json", "r", encoding="utf-8") as f:
            MAPPINGS = json.load(f)
    except:
        pass

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
            raw_t1 = parts[0].strip()
            raw_t2 = parts[1].strip()
            # Apply Mappings
            self.team1 = MAPPINGS.get(raw_t1, raw_t1)
            self.team2 = MAPPINGS.get(raw_t2, raw_t2)
        else:
            self.team1 = MAPPINGS.get(self.game, self.game)
            self.team2 = ""
            
        # Standardize date to YYYY-MM-DD
        self.date = self._normalize_date(str(self.date_raw))

    def _normalize_date(self, d):
        try:
            d = str(d).strip()
            # Winner format: 251226 (YYMMDD)
            if len(d) == 6 and d.isdigit():
                return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
            # Pinnacle format: 2025-12-26T20:00:00Z
            if 'T' in d:
                return d.split('T')[0]
            # Standard YYYY-MM-DD HH:MM -> YYYY-MM-DD
            if ' ' in d:
                # Check for "DD MMM YYYY" e.g. "03 Jan 2026"
                try:
                    parts = d.split()
                    if len(parts) >= 3:
                         date_str = " ".join(parts[:3])
                         return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
                except:
                    pass
                # Check for "YYYY-MM-DD HH:MM"
                if '-' in d:
                    return d.split(' ')[0]
            
            return d
        except:
            return d
            
    def get_key(self):
        return tuple(sorted([self.team1.lower(), self.team2.lower()]))

def check_favorite_flip(local: Game, remote: Game, remote_name: str = "Pinnacle"):
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
            f"{remote_name.lower()}_fav": pinnacle_fav_name,
            "winner_odds": {"1": local.num_1, "X": local.num_X, "2": local.num_2},
            f"{remote_name.lower()}_odds": {"1": remote.num_1, "X": remote.num_X, "2": remote.num_2},
            "remote_name": remote_name 
        }
    return None

from utils import _clean_team_name

def compare_games(winner_df: pd.DataFrame, remote_df: pd.DataFrame, remote_name: str = "Pinnacle"):
    winner_games = [Game(row.to_dict()) for index, row in winner_df.iterrows()]
    remote_games = [Game(row.to_dict()) for index, row in remote_df.iterrows()]
    
    # Index Remote games by date
    r_by_date = {}
    for g in remote_games:
        if g.date not in r_by_date: r_by_date[g.date] = []
        r_by_date[g.date].append(g)
        
    opportunities = []
    matched_count = 0
    matched_indices = []
    
    for i, w_game in enumerate(winner_games):
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
            
        potential_remote = []
        for d in target_dates:
            potential_remote.extend(r_by_date.get(d, []))

        if not potential_remote:
            continue
            
        best_match = None
        exact_match = None
        
        # 1. Look for exact match
        w_key = w_game.get_key()
        for r_game in potential_remote:
            if w_key == r_game.get_key():
                exact_match = r_game
                break
        
        if exact_match:
            best_match = exact_match
        else:
            # 2. Try Fuzzy Match team-by-team with normalized names
            max_overall_score = 0
            
            w1_clean = _clean_team_name(w_game.team1)
            w2_clean = _clean_team_name(w_game.team2)
            
            for r_game in potential_remote:
                p1_clean = _clean_team_name(r_game.team1)
                p2_clean = _clean_team_name(r_game.team2)
                
                # Calculate similarity for both orientations
                s1 = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
                s2 = difflib.SequenceMatcher(None, w2_clean, p2_clean).ratio()
                score_straight = (s1 + s2) / 2
                
                s3 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
                s4 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
                score_swapped = (s3 + s4) / 2
                
                # Validation: Both sides must have decent similarity to avoid "One strong match + Random"
                # e.g. "Valencia - Elche" vs "Celta - Valencia" (s4=1.0, s3=0.3) -> Avg=0.65 
                MIN_SIDE_SCORE = 0.75
                
                valid_straight = (s1 > MIN_SIDE_SCORE and s2 > MIN_SIDE_SCORE)
                valid_swapped = (s3 > MIN_SIDE_SCORE and s4 > MIN_SIDE_SCORE)
                
                best_score = 0
                if valid_straight:
                    best_score = score_straight
                if valid_swapped and score_swapped > best_score:
                    best_score = score_swapped
                
                # Using 0.82 as a safe cutoff for normalized name comparison
                if best_score > 0.82 and best_score > max_overall_score:
                    max_overall_score = best_score
                    best_match = r_game

        # 3. Global Fallback (Ignore Date if Name Score is VERY High) - Fixes "Today" Bug
        if not best_match:
            global_best_score = 0
            
            for r_game in remote_games:
                # Basic fuzzy check on teams (Copy-paste logic, ideally refactor but keeping inline for safety)
                p1_clean = _clean_team_name(r_game.team1)
                p2_clean = _clean_team_name(r_game.team2)
                
                s1 = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
                s2 = difflib.SequenceMatcher(None, w2_clean, p2_clean).ratio()
                score_straight = (s1 + s2) / 2
                
                s3 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
                s4 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
                score_swapped = (s3 + s4) / 2
                
                # Strict Validation for Global Fallback too
                valid_straight = (s1 > MIN_SIDE_SCORE and s2 > MIN_SIDE_SCORE)
                valid_swapped = (s3 > MIN_SIDE_SCORE and s4 > MIN_SIDE_SCORE)
                
                g_score = 0
                if valid_straight:
                    g_score = score_straight
                if valid_swapped and score_swapped > g_score:
                    g_score = score_swapped
                
                if g_score > global_best_score:
                    global_best_score = g_score
                    global_best_match = r_game
            
            # High threshold (0.88) to trust name over date
            if global_best_score > 0.88:
                best_match = global_best_match
                    
        if best_match:
            matched_count += 1
            matched_indices.append(i)
            
            # Determine if we need to swap Pinnacle's odds to match Winner's orientation
            # We compare the cleaned names used for matching
            w1_clean = _clean_team_name(w_game.team1)
            w2_clean = _clean_team_name(w_game.team2)
            
            p1_clean = _clean_team_name(best_match.team1)
            p2_clean = _clean_team_name(best_match.team2)
            
            # Strict Per-Team Odds Alignment
            # We determine explicitly which remote team matches W1 and W2.
            
            s_w1_r1 = difflib.SequenceMatcher(None, w1_clean, p1_clean).ratio()
            s_w1_r2 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
            
            s_w2_r1 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
            s_w2_r2 = difflib.SequenceMatcher(None, w2_clean, p2_clean).ratio()
            
            # Determine mapping
            # W1 maps to R1 if score R1 > score R2
            w1_maps_to = 1 if s_w1_r1 >= s_w1_r2 else 2
            w2_maps_to = 2 if s_w2_r2 >= s_w2_r1 else 1
            
            final_p_odds = {}
            is_valid_alignment = False
            is_swapped = False
            
            if w1_maps_to == 1 and w2_maps_to == 2:
                # Straight Match (W1->R1, W2->R2)
                final_p_odds = {
                    "num_1": best_match.num_1,
                    "num_X": best_match.num_X,
                    "num_2": best_match.num_2
                }
                is_valid_alignment = True
                
            elif w1_maps_to == 2 and w2_maps_to == 1:
                # Swapped Match (W1->R2, W2->R1)
                print(f"DEBUG: Strict Swap Detected for {w_game.game}")
                final_p_odds = {
                    "num_1": best_match.num_2, # W1 gets R2 odds
                    "num_X": best_match.num_X,
                    "num_2": best_match.num_1  # W2 gets R1 odds
                }
                is_valid_alignment = True
                is_swapped = True
            else:
                # Ambiguous match
                print(f"DEBUG: Ambiguous alignment for {w_game.game} vs {best_match.game}.")
                print(f"  W1: '{w1_clean}' | W2: '{w2_clean}'")
                print(f"  R1: '{p1_clean}' | R2: '{p2_clean}'")
                print(f"  Scores W1->Matches: R1={s_w1_r1:.2f}, R2={s_w1_r2:.2f} --> Maps to {w1_maps_to}")
                print(f"  Scores W2->Matches: R1={s_w2_r1:.2f}, R2={s_w2_r2:.2f} --> Maps to {w2_maps_to}")
                continue
                
            if not is_valid_alignment:
                continue

            # Create a virtual aligned Game for check_favorite_flip
            aligned_r_game = Game({
                "game": f"{w_game.team1} - {w_game.team2}",
                "date": best_match.date,
                "num_1": final_p_odds["num_1"],
                "num_X": final_p_odds["num_X"],
                "num_2": final_p_odds["num_2"],
                "link": best_match.link
            })
            
            res = check_favorite_flip(w_game, aligned_r_game, remote_name=remote_name)
            if res:
                if is_swapped:
                    res['is_swapped'] = True
                    # Store original odds for display
                    res['original_remote_odds'] = {
                        "num_1": best_match.num_1,
                        "num_X": best_match.num_X,
                        "num_2": best_match.num_2
                    }
            
            if res:
                # Add remote team names for display
                res['remote_team1'] = best_match.team1
                res['remote_team2'] = best_match.team2
                opportunities.append(res)
    
    return opportunities, matched_count, matched_indices
