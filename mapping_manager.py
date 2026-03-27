import json
import os
import difflib
from datetime import datetime, timedelta
from pathlib import Path
from utils import _clean_team_name

DATA_DIR = Path(__file__).parent / "data"
NAME_MAPPINGS_FILE = DATA_DIR / "name_mappings.json"
PENDING_MAPPINGS_FILE = DATA_DIR / "pending_mappings.json"

# Priority enum: higher number = higher priority
SOURCE_PRIORITY = {
    "Unibet Inference": 4,
    "Pinnacle Inference": 3,
    "Translated": 2,
    "Legacy Unverified": 1
}

class MappingManager:
    def __init__(self):
        self.verified_mappings = {}
        self.pending_mappings = {}
        self.load_mappings()

    def load_mappings(self):
        if NAME_MAPPINGS_FILE.exists():
            try:
                with open(NAME_MAPPINGS_FILE, "r", encoding="utf-8") as f:
                    self.verified_mappings = json.load(f)
            except Exception as e:
                print(f"Error loading {NAME_MAPPINGS_FILE}: {e}")
        
        if PENDING_MAPPINGS_FILE.exists():
            try:
                with open(PENDING_MAPPINGS_FILE, "r", encoding="utf-8") as f:
                    self.pending_mappings = json.load(f)
            except Exception as e:
                print(f"Error loading {PENDING_MAPPINGS_FILE}: {e}")

    def _write_verified(self):
        try:
            with open(NAME_MAPPINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.verified_mappings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to write verified mappings: {e}")

    def get_translation(self, hebrew_name, current_league=""):
        # 1. Check verified
        if hebrew_name in self.verified_mappings:
            val = self.verified_mappings[hebrew_name]
            if isinstance(val, dict):
                # Auto-fill empty leagues context
                if current_league and val.get("league") == "":
                    val["league"] = current_league
                    self._write_verified()
                    try:
                        from stats_manager import StatsManager
                        StatsManager().add_names_auto_mapped_with_league(1)
                    except Exception as e:
                        pass
                return val.get("english", hebrew_name)
            else:
                return val
            
        # 2. Check pending
        if hebrew_name in self.pending_mappings:
            val = self.pending_mappings[hebrew_name]
            if isinstance(val, dict):
                return val.get("english_name", hebrew_name)
            else:
                return val
                
        return None

    def save_pending(self, hebrew_name, english_name, source):
        if not english_name:
            return
            
        # Prevent overwriting verified mappings
        if hebrew_name in self.verified_mappings:
            return

        current = self.pending_mappings.get(hebrew_name)
        
        should_update = False
        if not current:
            should_update = True
        else:
            current_source = "Legacy Unverified"
            if isinstance(current, dict):
                current_source = current.get("source", "Legacy Unverified")
                
            new_priority = SOURCE_PRIORITY.get(source, 0)
            current_priority = SOURCE_PRIORITY.get(current_source, 0)
            
            if new_priority > current_priority:
                should_update = True
                
        if should_update:
            self.pending_mappings[hebrew_name] = {
                "english_name": english_name,
                "source": source
            }
            self._write_pending()

    def _write_pending(self):
        try:
            with open(PENDING_MAPPINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.pending_mappings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to write pending mappings: {e}")

    def infer_mappings(self, winner_df, remote_df, remote_name="Unibet", source_label="Unibet Inference"):
        """
        Attempts to infer unmapped Hebrew names by matching against remote_df
        based on date and the *other* team in the matchup which IS known.
        """
        if winner_df is None or winner_df.empty or remote_df is None or remote_df.empty:
            return 0

        remote_by_date = {}
        for _, row in remote_df.iterrows():
            d = str(row.get('date', '')).split('T')[0]
            if ' ' in d: d = d.split(' ')[0]
            if d not in remote_by_date:
                remote_by_date[d] = []
            
            game_str = str(row.get('game', ''))
            if ' - ' in game_str:
                t1, t2 = game_str.split(' - ', 1)
                remote_by_date[d].append((t1.strip(), t2.strip()))

        count = 0
        
        for _, row in winner_df.iterrows():
            hebrew_game = str(row.get('hebrew_game', ''))
            english_game = str(row.get('game', ''))
            w_date = str(row.get('date', ''))
            
            if len(w_date) == 6 and w_date.isdigit():
                w_date = f"20{w_date[0:2]}-{w_date[2:4]}-{w_date[4:6]}"
            
            if ' - ' not in hebrew_game or ' - ' not in english_game:
                continue
                
            h_t1, h_t2 = [x.strip() for x in hebrew_game.split(' - ', 1)]
            e_t1, e_t2 = [x.strip() for x in english_game.split(' - ', 1)]
            
            t1_needs_inference = h_t1 not in self.verified_mappings
            t2_needs_inference = h_t2 not in self.verified_mappings
            
            if not t1_needs_inference and not t2_needs_inference:
                continue 
                
            if t1_needs_inference and t2_needs_inference:
                continue
                
            if t1_needs_inference:
                known_hebrew = h_t2
                known_english = e_t2
                unknown_hebrew = h_t1
                unknown_pos = 0 
            else:
                known_hebrew = h_t1
                known_english = e_t1
                unknown_hebrew = h_t2
                unknown_pos = 1 

            target_dates = [w_date]
            try:
                dt = datetime.strptime(w_date, "%Y-%m-%d")
                target_dates.append((dt - timedelta(days=1)).strftime("%Y-%m-%d"))
                target_dates.append((dt + timedelta(days=1)).strftime("%Y-%m-%d"))
            except:
                pass
                
            candidates = []
            for d in target_dates:
                candidates.extend(remote_by_date.get(d, []))
                
            best_match_remote_team = None
            highest_score = 0
            
            known_clean = _clean_team_name(known_english)
            if not known_clean:
                continue
            
            for (r_t1, r_t2) in candidates:
                r_t1_clean = _clean_team_name(r_t1)
                r_t2_clean = _clean_team_name(r_t2)
                
                # Check straight match
                if unknown_pos == 0:
                    score = difflib.SequenceMatcher(None, known_clean, r_t2_clean).ratio()
                    if score > 0.85 and score > highest_score:
                        highest_score = score
                        best_match_remote_team = r_t1
                else:
                    score = difflib.SequenceMatcher(None, known_clean, r_t1_clean).ratio()
                    if score > 0.85 and score > highest_score:
                        highest_score = score
                        best_match_remote_team = r_t2
                        
                # Check swapped match
                if unknown_pos == 0:
                    score = difflib.SequenceMatcher(None, known_clean, r_t1_clean).ratio()
                    if score > 0.85 and score > highest_score:
                        highest_score = score
                        best_match_remote_team = r_t2
                else: 
                    score = difflib.SequenceMatcher(None, known_clean, r_t2_clean).ratio()
                    if score > 0.85 and score > highest_score:
                        highest_score = score
                        best_match_remote_team = r_t1
                        
            if best_match_remote_team and highest_score > 0.85:
                # Need to verify that the extracted name isn't just known_clean again
                if difflib.SequenceMatcher(None, _clean_team_name(best_match_remote_team), known_clean).ratio() < 0.8:
                    self.save_pending(unknown_hebrew, best_match_remote_team, source_label)
                    count += 1
                
        return count

mapping_manager = MappingManager()
