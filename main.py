
"""""
from calculations import compare_games
from message import bet_notifications
from winner_odds import *
import asyncio
import sqlite3

RUN_INTERVAL_SECONDS = 300


def get_db(db_link="data/winner_data.sqlite", command="SELECT * FROM 'games'"):
    conn = sqlite3.connect(db_link)
    ls = conn.execute(command).fetchall()
    conn.close()
    return ls


if __name__ == "__main__":
    while True:
        end_date = asyncio.run(activate_bot())
        winner_list = get_db()
        lst = compare_games(winner_list)
        for bet in lst:
            bet_notifications(odds_data=bet)
        print(f"Waiting {RUN_INTERVAL_SECONDS} seconds until next run...")
        time.sleep(RUN_INTERVAL_SECONDS)
"""""


from calculations import compare_games
from message import bet_notifications
from winner_odds import *
import sqlite3
import time
import logging

RUN_INTERVAL_SECONDS = 120

# הגדרת לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db(db_link="data/winner_data.sqlite", command="SELECT * FROM 'games'"):
    try:
        conn = sqlite3.connect(db_link)
        ls = conn.execute(command).fetchall()
        conn.close()
        logger.info(f"✅ Loaded {len(ls)} games from the database.")
        return ls
    except Exception as e:
        logger.error(f"❌ Error reading from database: {e}")
        return []


if __name__ == "__main__":
    while True:
        try:
            logger.info("🚀 Starting new run...")

            # שלב 1: הפעלת הבוט ואיסוף נתונים מהאתר
            end_date = activate_bot()  # ✅ תוקן! בלי asyncio.run
            logger.info(f"✅ Finished scraping. Last game date: {end_date}")

            # שלב 2: שליפת נתוני Winner
            winner_list = get_db()

            # שלב 3: השוואת משחקים לחיפוש הזדמנויות
            lst = compare_games(winner_list)
            logger.info(f"🎯 Found {len(lst)} betting opportunities.")

            # שלב 4: שליחת התראות בטלגרם
            for bet in lst:
                try:
                    bet_notifications(odds_data=bet)
                    logger.info(f"📤 Notification sent: {bet}")
                except Exception as e:
                    logger.error(f"❌ Error sending notification: {e}")

            logger.info(f"⌛ Waiting {RUN_INTERVAL_SECONDS} seconds until next run...")
            time.sleep(RUN_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            logger.info(f"⌛ Waiting {RUN_INTERVAL_SECONDS} seconds before retrying...")
            time.sleep(RUN_INTERVAL_SECONDS)
