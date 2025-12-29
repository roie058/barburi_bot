# בוט ששולח הודעות בטלגרם - עובד
import requests
import os

# Define the password
PASSWORD = "1234"
AUTHORIZED_USERS = set()

# Telegram bot credentials - Replace with your own details
TELEGRAM_BOT_TOKEN = "7599624940:AAF93dleDtTSNCpZxkcgvJh4ZA-l1WbzU2w"


def message_all_users(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Path to authorized users
    auth_path = "data/authorized_users.txt"
    if not os.path.exists(auth_path):
        # Try sibling if running from scripts
        auth_path = "../data/authorized_users.txt"
        
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
    w_odds = odds_data['winner_odds']
    p_odds = odds_data['pinnacle_odds']
    
    message = (
        f"🔥 Betting Alert! 🔥\n\n"
        f"🎯 Match: {odds_data['game']}\n"
        f"📅 Date: {odds_data['date']}\n\n"
        f"💰 Bet on: {odds_data['pinnacle_fav']}\n"
        f"📊 Gap: {odds_data['gap']}\n\n"
        f"Winner Odds:\n1: {w_odds['1']} | X: {w_odds['X']} | 2: {w_odds['2']}\n\n"
        f"Pinnacle Odds:\n1: {p_odds['1']} | X: {p_odds['X']} | 2: {p_odds['2']}\n"
    )

    # Telegram API URL for sending the message
    message_all_users(message)
