import pandas as pd
from datetime import datetime
import difflib
import json
import os
import sys

# Mock classes to reproduce logic exactly
class Game:
    def __init__(self, data):
        self.game = data.get('game', '')
        self.date_raw = data.get('date', '')
        self.link = data.get('link', '')
        
        # Normalize teams (Simplified for debug, assuming no mapping loaded for now or manual)
        if ' - ' in self.game:
            parts = self.game.split(' - ')
            self.team1 = parts[0].strip()
            self.team2 = parts[1].strip()
        else:
            self.team1 = self.game
            self.team2 = ""
            
        self.date = self._normalize_date(str(self.date_raw))

    def _normalize_date(self, d):
        try:
            d = str(d).strip()
            # Winner format: 260117
            if len(d) == 6 and d.isdigit():
                return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
            # Unibet format: "17 Jan 2026 14:30"
            if ' ' in d:
                try:
                    parts = d.split()
                    if len(parts) >= 3:
                         date_str = " ".join(parts[:3])
                         return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
                except:
                    pass
            return d
        except:
            return d

    def get_key(self):
        return tuple(sorted([self.team1.lower(), self.team2.lower()]))

def debug_match():
    # 1. Setup Data exactly as suspected
    winner_row = {
        "game": "Manchester United - Manchester City",
        "date": "260117", # YYMMDD
        "num_1": 3.25, "num_X": 3.65, "num_2": 1.9,
        "link": "winner.co.il"
    }
    
    unibet_row = {
        "game": "Manchester United - Manchester City",
        "date": "17 Jan 2026 14:30", # From logs
        "num_1": 3.25, "num_X": 3.65, "num_2": 1.9,
        "link": "unibet"
    }

    w_game = Game(winner_row)
    u_game = Game(unibet_row)
    
    print(f"Winner Game: {w_game.game} | Date: {w_game.date_raw} -> {w_game.date}")
    print(f"Unibet Game: {u_game.game} | Date: {u_game.date_raw} -> {u_game.date}")
    
    # 2. Key Check
    w_key = w_game.get_key()
    u_key = u_game.get_key()
    
    print(f"Winner Key: {w_key}")
    print(f"Unibet Key: {u_key}")
    
    if w_key == u_key:
        print("KEYS MATCH! (Exact match logic works)")
    else:
        print("KEYS DO NOT MATCH.")
        
    # 3. Date Logic Check
    w_dt = datetime.strptime(w_game.date, "%Y-%m-%d")
    from datetime import timedelta
    target_dates = [
        (w_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
        w_game.date,
        (w_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    ]
    print(f"Target Dates: {target_dates}")
    
    if u_game.date in target_dates:
        print(f"DATE MATCH! Unibet date {u_game.date} is in target range.")
    else:
        print(f"DATE FAIL! Unibet date {u_game.date} NOT in {target_dates}")

if __name__ == "__main__":
    debug_match()
