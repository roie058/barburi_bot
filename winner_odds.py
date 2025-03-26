
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import sqlite3
from googletrans import Translator


def scroll_down(drive):
    """A method for scrolling the page."""
    # Get scroll height.
    last_height = drive.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to the bottom.
        drive.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load the page.
        time.sleep(2)
        # Calculate new scroll height and compare with last scroll height.
        new_height = drive.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


async def translate_team_name(team_name):
    translator = Translator()
    return await translator.translate(team_name, src="iw", dest="en")


def save_df_to_sql(col, lst, db="data/winner_data.sqlite", tbl="games", exist="replace"):
    # שמירת הנתונים כ-DataFrame
    df = pd.DataFrame(lst, columns=col)
    conn = sqlite3.connect(db)
    df.to_sql(tbl, conn, if_exists=exist, index=False)
    # סגירת החיבור למסד הנתונים
    conn.close()


def get_db(db_link="data/winner_data.sqlite", command="SELECT * FROM 'games'"):
    conn = sqlite3.connect(db_link)
    ls = conn.execute(command).fetchall()
    conn.close()
    return ls


def load_team_names():
    conn = sqlite3.connect("data/name_db.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT he, en FROM names")
    names = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return names


team_names_cache = load_team_names()


async def get_team_name(heb):
    if heb in team_names_cache:
        return team_names_cache[heb]
    en = await translate_team_name(heb)  # פונקציה רגילה, לא `async`
    team_names_cache[heb] = en.text
    save_df_to_sql(['en', 'he'], [[en.text, heb]], "data/name_db.sqlite", 'names', "append")
    save_df_to_sql(['en', 'he'], [[en.text, heb]], "data/new_names_db.sqlite", 'names', "append")
    return en.text


def get_driver():
    options = webdriver.ChromeOptions()
    # options.binary_location = "/usr/bin/chromium"

    # הפעלת מצב Headless
    options.add_argument("--headless=new")  # `new` תומך טוב יותר באתרים מודרניים
    options.add_argument("--no-sandbox")  # חשוב בסביבות שרתים
    options.add_argument("--disable-dev-shm-usage")  # מונע קריסות בזיכרון משותף
    options.add_argument("--disable-gpu")  # מונע בעיות גרפיות
    options.add_argument("--window-size=1920,1080")  # מבטיח טעינה מלאה
    # options.add_argument("--remote-debugging-port=9222")  # למניעת DevToolsActivePort
    # options.add_argument("--disable-blink-features=AutomationControlled")  # להסתיר את הסקרייפר
    # options.add_argument('--proxy-server=http://51.16.179.113:1080')
    # מגדיר User-Agent כדי למנוע חסימות
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    #service = Service("/home/Barburi25/chromedriver")  # נתיב מתאים
    service = Service(ChromeDriverManager().install())  # נתיב מתאים

    driver = webdriver.Chrome(service=service, options=options)
    # time.sleep(5)  # לחכות לטעינת הדף
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # גלילה להפעיל טעינת JS
    # time.sleep(2)
    return driver


def safe_find(element, by, value, default=""):
    try:
        return element.find_element(by, value).text.strip()
    except Exception as e:
        return default


async def activate_bot():
    # הגדרת דרייבר
    driver = get_driver()
    time.sleep(3)
    # פתיחת האתר
    driver.get(
        "https://www.winner.co.il/%D7%9E%D7%A9%D7%97%D7%A7%D7%99%D7%9D/%D7%95%D7%95%D7%99%D7%A0%D7%A8-%D7%9C%D7%99%D7%99"
        "%D7%9F/%D7%94%D7%99%D7%95%D7%9D/%D7%9B%D7%9C-%D7%94%D7%9E%D7%93%D7%99%D7%A0%D7%95%D7%AA/%D7%9B%D7%9C-%D7%94%D7"
        "%9C%D7%99%D7%92%D7%95%D7%AA/10002@239~10002@240~50002@227~610005@240~610005@240~610005@240~610005@240~9990002"
        "@227~9990002@227~9990002@227~9990002@227")  # יש להחליף באתר הרלוונטי

    # המתנה לטעינת האלמנטים
    wait = WebDriverWait(driver, 40)
    wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='כל הימים']"))).click()
    scroll_down(driver)

    # איתור כל המשחקים
    matches = []
    all_markets = driver.find_elements(By.CLASS_NAME, "MARKET_TYPE_HEADER")
    for market in all_markets:
        game_type = safe_find(market, By.CLASS_NAME, "market-date-x")
        # שינוי בהתאם למבנה
        item_leagues = market.find_elements(By.CLASS_NAME, "item-leagues")
        current_date = None
        for league_container in item_leagues:
            elements = league_container.find_elements(By.XPATH, "./div/div")
            for elem in elements:

                if not elem.get_attribute("class"):  # זהו תאריך חדש
                    current_date = safe_find(elem, By.XPATH, "./div/span/span[3]", default=current_date)
                elif "LEAGUE_HEADER" in elem.get_attribute("class"):  # זה ליגה חדשה
                    league_header = elem.find_element(By.CLASS_NAME, "league-header")
                    league_name = safe_find(league_header, By.TAG_NAME, 'span')
                    game_container = elem.find_element(By.CLASS_NAME, "markets-container")
                    games = game_container.find_elements(By.CLASS_NAME, "market")  # שינוי בהתאם למבנה
                    for game in games:
                        game_time = safe_find(game, By.CLASS_NAME, 'time')
                        odds = game.find_elements(By.CLASS_NAME, 'outcome')
                        fulldate = current_date.split('.')
                        formatted_date = f"{datetime.datetime.now().year}-{fulldate[1]}-{fulldate[0]}"
                        match_data = [
                            game_type,
                            league_name,
                            formatted_date,
                            game_time,
                        ]
                        for odd in odds:
                            try:
                                team_span = safe_find(odd, By.CLASS_NAME, 'hasHebrewCharacters')
                                if len(team_span) == 0:
                                    continue
                                ratio = safe_find(odd, By.CLASS_NAME, 'ratio')
                                team_name = await get_team_name(team_span)
                                if len(match_data) < 8:
                                    match_data = match_data + [team_name, ratio]
                            except Exception as e:
                                continue
                        if len(match_data) == 8:
                            print(match_data)
                            matches.append(match_data)
                        else:
                            print("נתונים לא תקינים למשחק:", match_data)

    # סגירת הדרייבר
    driver.quit()
    columns = ["game_type",
               "league_name",
               "game_date",
               "game_time", 'Team1', "Outcome1", 'Team2', "Outcome2"]
    save_df_to_sql(columns, matches)
    last_date = get_db(command="SELECT max(game_date) from games;")
    return last_date[0][0]
