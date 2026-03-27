import json
import os
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'telemetry_state.json')

class StatsManager:
    def __init__(self):
        self.state = {
            "cumulative": {
                "new_games_recorded": 0,
                "games_changed": 0,
                "names_inferred": 0,
                "leagues_needing_mapping": 0
            },
            "last_run": {
                "timestamp": "Never",
                "status": "WAITING",
                "winner_matches": 0,
                "unibet_matches": 0,
                "pinnacle_matches": 0,
                "unibet_matches_matched": 0,
                "pinnacle_matches_matched": 0,
                "error_message": ""
            }
        }
        self._load()

    def _load(self):
        """Load state from JSON if it exists."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    saved_state = json.load(f)
                    
                    # Merge loaded state carefully to preserve structure
                    if "cumulative" in saved_state:
                        self.state["cumulative"].update(saved_state["cumulative"])
                    if "last_run" in saved_state:
                        self.state["last_run"].update(saved_state["last_run"])
            except Exception as e:
                print(f"StatsManager: Failed to load state from {STATE_FILE}: {e}")

    def _save(self):
        """Save current state to JSON."""
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"StatsManager: Failed to save state to {STATE_FILE}: {e}")

    # --- Cumulative Setters ---
    
    def add_new_games(self, count):
        self._load() # Ensure we sync up first
        self.state["cumulative"]["new_games_recorded"] += count
        self._save()

    def add_games_changed(self, count):
        self._load()
        self.state["cumulative"]["games_changed"] += count
        self._save()

    def add_names_inferred(self, count):
        self._load()
        self.state["cumulative"]["names_inferred"] += count
        self._save()

    def set_leagues_needing_mapping(self, count):
        self._load()
        self.state["cumulative"]["leagues_needing_mapping"] = count
        self._save()

    # --- Last Run Setters ---

    def set_last_run_success(self, winner, unibet, pinnacle, u_matched, p_matched):
        self._load()
        self.state["last_run"] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "SUCCESS",
            "winner_matches": winner,
            "unibet_matches": unibet,
            "pinnacle_matches": pinnacle,
            "unibet_matches_matched": u_matched,
            "pinnacle_matches_matched": p_matched,
            "error_message": ""
        }
        self._save()

    def set_last_run_failed(self, error_message):
        self._load()
        self.state["last_run"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state["last_run"]["status"] = "FAILED"
        self.state["last_run"]["error_message"] = str(error_message)[:100]
        self._save()

    # --- Telegraph / Telegram Accessors ---

    def reset_cumulative(self):
        self._load()
        self.state["cumulative"] = {
            "new_games_recorded": 0,
            "games_changed": 0,
            "names_inferred": 0,
            "leagues_needing_mapping": 0
        }
        self._save()

    def get_status_message(self):
        self._load()
        c = self.state["cumulative"]
        lr = self.state["last_run"]
        
        msg = "📊 *Barburi Bot Status Report* 📊\n\n"
        
        msg += "📈 *Activity Since Last Report:*\n"
        msg += f"🔸 New Games Recorded: {c['new_games_recorded']}\n"
        msg += f"🔸 Game Odds Changed: {c['games_changed']}\n"
        msg += f"🔸 Names Inferred: {c['names_inferred']}\n"
        msg += f"🔸 Leagues Needing Mapping: {c['leagues_needing_mapping']}\n\n"
        
        msg += "⏱ *Last Run Metrics:*\n"
        msg += f"Status: {'✅ SUCCESS' if lr['status'] == 'SUCCESS' else '❌ FAILED'}\n"
        msg += f"Time: {lr['timestamp']}\n\n"
        
        if lr['status'] == 'FAILED':
            msg += f"Error: `{lr['error_message']}`\n"
        else:
            msg += f"⚽ Winner Matches Scraped: {lr['winner_matches']}\n"
            msg += f"🟩 Unibet Matches Scraped: {lr['unibet_matches']}\n"
            msg += f"🟩 Unibet Matches Cross-Referenced: {lr['unibet_matches_matched']}\n"
            msg += f"🟧 Pinnacle Matches Scraped: {lr['pinnacle_matches']}\n"
            msg += f"🟧 Pinnacle Matches Cross-Referenced: {lr['pinnacle_matches_matched']}\n"
            
        return msg
