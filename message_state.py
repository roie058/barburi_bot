import json
import os
from datetime import datetime

STATE_FILE = "data/sent_notifications.json"

def load_sent_notifications():
    if not os.path.exists("data"):
        os.makedirs("data", exist_ok=True)
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_sent_notifications(sent_dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(sent_dict, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving notification state: {e}")

def get_match_id(opp):
    """
    Creates a unique ID for a match based on its teams and date.
    Teams are sorted to ensure 'A-B' and 'B-A' match.
    """
    game_str = opp.get('game', '')
    date_str = opp.get('date', '')
    
    teams = game_str.split(' - ')
    if len(teams) == 2:
        sorted_teams = "-".join(sorted([t.strip().lower() for t in teams]))
    else:
        sorted_teams = game_str.lower()
        
    return f"{date_str}_{sorted_teams}"

def should_send_notification(opp):
    sent_dict = load_sent_notifications()
    match_id = get_match_id(opp)
    
    if match_id in sent_dict:
        return False
    return True

def mark_notification_sent(opp):
    sent_dict = load_sent_notifications()
    match_id = get_match_id(opp)
    sent_dict[match_id] = datetime.now().isoformat()
    
    # Cleanup: Remove entries older than 3 days to keep file small
    # (Optional, but good practice)
    now = datetime.now()
    to_delete = []
    for mid, timestamp in sent_dict.items():
        try:
            ts = datetime.fromisoformat(timestamp)
            if (now - ts).days > 3:
                to_delete.append(mid)
        except:
            pass
    for mid in to_delete:
        del sent_dict[mid]
        
    save_sent_notifications(sent_dict)
