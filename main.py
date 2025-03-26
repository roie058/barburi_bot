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
