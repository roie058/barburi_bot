# בוט ששולח הודעות בטלגרם - עובד
import requests
import os
from config import TELEGRAM_BOT_TOKEN, BOT_PASSWORD, AUTHORIZED_USERS_FILE

# Define the password
PASSWORD = BOT_PASSWORD

def message_all_users(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Path to authorized users
    auth_path = AUTHORIZED_USERS_FILE
        
    if not os.path.exists(auth_path):
        print(f"Error: Authorized users file not found at {auth_path}")
        return

    try:
        with open(auth_path, "r") as file:
            for line in file:
                line = line.strip()
                if not line: continue
                
                try:
                    user_id = int(line)
                except ValueError:
                    continue
                    
                # Prepare the payload for the request
                payload = {
                    "chat_id": user_id,
                    "text": msg,
                    "# parse_mode": "Markdown" # Markdown can break if special chars are present in teams. Disabling for safety or use HTML.
                }

                # Send the request
                try:
                    response = requests.post(url, data=payload)
                    response.raise_for_status()
                    print(f"Notification sent to {user_id} successfully!")
                except requests.exceptions.RequestException as e:
                    print("An error occurred while sending the notification:", e)
    except Exception as e:
        print(f"Error reading authorized users: {e}")


def bet_notifications(odds_data):
    """
    Sends a formatted message to Telegram based on the 'Favorite Flip' data structure.
    """
    # Construct the detailed message
    # User Request: "Betting Alert", No Pinnacle Fav, Keep Winner Fav.
    
    # Format odds for cleanliness
    # Format odds for cleanliness
    w_odds = odds_data['winner_odds']
    
    remote_name = odds_data.get('remote_name', 'Pinnacle')
    remote_key_odds = f"{remote_name.lower()}_odds" # e.g. pinnacle_odds or unibet_odds
    remote_key_fav = f"{remote_name.lower()}_fav"
    
    # Fallback for old style if needed
    if remote_key_odds not in odds_data:
         # Try default pinnacle
         remote_key_odds = 'pinnacle_odds'
         remote_key_fav = 'pinnacle_fav'
         remote_name = 'Pinnacle'
    
    r_odds = odds_data.get(remote_key_odds, {})
    
    swapped_msg = " (Swapped)" if odds_data.get('is_swapped') else ""
    
    orig_odds_str = ""
    if odds_data.get('is_swapped') and 'original_remote_odds' in odds_data:
        oo = odds_data['original_remote_odds']
        orig_odds_str = f"Original {remote_name} Odds:\n1: {oo.get('1')} | X: {oo.get('X')} | 2: {oo.get('2')}\n"
    
    message = (
        f"🔥 Betting Alert! 🔥\n\n"
        f"🎯 Match: {odds_data['game']}\n"
        f"📅 Date: {odds_data['date']}\n\n"
        f"💰 Bet on: {odds_data.get(remote_key_fav, 'Unknown')}\n"
        f"📊 Gap: {odds_data['gap']}\n\n"
        f"Winner Odds:\n1: {w_odds.get('1')} | X: {w_odds.get('X')} | 2: {w_odds.get('2')}\n\n"
        f"{remote_name} Odds{swapped_msg}:\n1: {r_odds.get('1')} | X: {r_odds.get('X')} | 2: {r_odds.get('2')}\n"
        f"{orig_odds_str}"
    )

    # Telegram API URL for sending the message
    message_all_users(message)

def major_change_notification(odds_data):
    """
    Sends a formatted message to Telegram for a MAJOR odds change in Winner.
    """
    w_old_odds = odds_data['old_winner_odds']
    w_new_odds = odds_data['new_winner_odds']
    
    remote_names_str = ""
    # Add remote odds if available
    for remote in ["Unibet", "Pinnacle"]:
        r_key = f"{remote.lower()}_odds"
        if r_key in odds_data and odds_data[r_key]:
            r_odds = odds_data[r_key]
            remote_names_str += f"\n{remote} Odds:\n1: {r_odds.get('1')} | X: {r_odds.get('X')} | 2: {r_odds.get('2')}\n"
            
    message = (
        f"🚨 MAJOR ODDS CHANGE 🚨\n\n"
        f"🎯 Match: {odds_data['game']}\n"
        f"📅 Date: {odds_data['date']}\n\n"
        f"⚠️ Favorite Flipped or Shifted Significantly!\n\n"
        f"Old Winner Odds:\n1: {w_old_odds['1']} | X: {w_old_odds['X']} | 2: {w_old_odds['2']}\n\n"
        f"New Winner Odds:\n1: {w_new_odds['1']} | X: {w_new_odds['X']} | 2: {w_new_odds['2']}\n"
        f"{remote_names_str}"
    )

    message_all_users(message)
