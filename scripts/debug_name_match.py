import difflib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import _clean_team_name

def debug_name_match():
    # Simulate the scenario from the logs
    w_team1 = "Al-Shabab"
    w_team2 = "Al-Najma"
    
    p_team1 = "Al-Nassr"
    p_team2 = "Al-Shabab"
    
    print(f"Comparing Winner: '{w_team1}' vs '{w_team2}'")
    print(f"       vs Pinnacle: '{p_team1}' vs '{p_team2}'")
    
    # 1. Clean Names
    w1_clean = _clean_team_name(w_team1)
    w2_clean = _clean_team_name(w_team2)
    p1_clean = _clean_team_name(p_team1)
    p2_clean = _clean_team_name(p_team2)
    
    print(f"Cleaned W: '{w1_clean}', '{w2_clean}'")
    print(f"Cleaned P: '{p1_clean}', '{p2_clean}'")
    
    # 2. Score Calculation (Swapped)
    # W1 (Shabab) -> P2 (Shabab)
    s3 = difflib.SequenceMatcher(None, w1_clean, p2_clean).ratio()
    # W2 (Najma) -> P1 (Nassr)
    s4 = difflib.SequenceMatcher(None, w2_clean, p1_clean).ratio()
    
    swap_score = (s3 + s4) / 2
    
    print(f"Score W1(Shabab)->P2(Shabab): {s3:.4f}")
    print(f"Score W2(Najma)->P1(Nassr): {s4:.4f}")
    print(f"AVG Swapped Score: {swap_score:.4f}")
    
    if swap_score > 0.65:
        print("MATCH! (This confirms why the bot matched them)")
    else:
        print("NO MATCH (Score too low)")

if __name__ == "__main__":
    debug_name_match()
