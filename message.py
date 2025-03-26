# בוט ששולח הודעות בטלגרם - עובד
import requests

# Define the password
PASSWORD = "1234"
AUTHORIZED_USERS = set()

# Telegram bot credentials - Replace with your own details
TELEGRAM_BOT_TOKEN = "7599624940:AAF93dleDtTSNCpZxkcgvJh4ZA-l1WbzU2w"


def message_all_users(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    with open("data/authorized_users.txt", "r") as file:
        for line in file:
            user_id = int(line.strip())  # שמירת ה-Chat ID כמספר
            # Prepare the payload for the request
            payload = {
                "chat_id": user_id,
                "text": msg,
                "parse_mode": "Markdown"  # נסה גם "HTML" במידת הצורך
            }

            # Send the request
            try:
                response = requests.post(url, data=payload)
                response.raise_for_status()  # Raise an error if the request failed
                print("Notification sent successfully!")
            except requests.exceptions.RequestException as e:
                print("An error occurred while sending the notification:", e)
                # print("Response from Telegram:", response.text)
        file.close()


def bet_notifications(odds_data):
    # This function receives betting odds data for a football match and sends a notification via Telegram.
    # Construct the detailed message
    message = f"🔥{odds_data['bet_type']} Betting Opportunity Found! 🔥\n\n" \
              f"🎯 Game: {odds_data['team1']} vs {odds_data['team2']}\n\n" \
              f"📅 Date: {odds_data['game_date']}\n\n" \
              f"International Odds :  {odds_data['int_team1']} {odds_data['int_odd1']} - {odds_data['int_team2']}" \
              f" {odds_data['int_odd2']}\n\n" \
              f"Winner Odds : {odds_data['team1']} {odds_data['local_odd1']} - {odds_data['team2']} " \
              f"{odds_data['local_odd2']}\n\n" \
              f"💰 Bet on: {odds_data['bet_on_team']}\n\n"

    # Telegram API URL for sending the message
    message_all_users(message)
