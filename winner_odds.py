import datetime
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import sqlite3
from googletrans import Translator
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scroll_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def translate_team_name(team_name):
    translator = Translator()
    return translator.translate(team_name, src="iw", dest="en")


def save_df_to_sql(col, lst, db="data/winner_data.sqlite", tbl="games", exist="replace"):
    df = pd.DataFrame(lst, columns=col)
    conn = sqlite3.connect(db)
    df.to_sql(tbl, conn, if_exists=exist, index=False)
    conn.close()
    logger.info(f"Saved {len(df)} records to {tbl}.")


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


def get_team_name(heb):
    if heb in team_names_cache:
        return team_names_cache[heb]
    try:
        en = translate_team_name(heb)
        team_names_cache[heb] = en.text
        save_df_to_sql(['en', 'he'], [[en.text, heb]], "data/name_db.sqlite", 'names', "append")
        save_df_to_sql(['en', 'he'], [[en.text, heb]], "data/new_names_db.sqlite", 'names', "append")
        logger.info(f"Translated and saved team name: {heb} -> {en.text}")
        return en.text
    except Exception as e:
        logger.error(f"Error translating team name {heb}: {e}")
        return heb


def get_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                   Object.defineProperty(navigator, 'webdriver', {
                     get: () => undefined
                   })
                 """
    })

    return driver


def safe_find(element, by, value, default=""):
    try:
        return element.find_element(by, value).text.strip()
    except Exception:
        return default


def activate_bot():
    logger.info("Starting activate_bot...")
    driver = get_driver()
    time.sleep(3)

    try:
        url = "https://www.winner.co.il/משחקים/ווינר-ליין/היום/כל-המדינות/כל-הליגות/"
        driver.get(url)
        logger.info(f"Opened URL: {url}")

        wait = WebDriverWait(driver, 40)
        try:
            button = wait.until(EC.presence_of_element_located((By.XPATH, "//h2[text()='כל הימים']")))
            button.click()
            logger.info("Clicked 'כל הימים' button successfully.")
        except TimeoutException:
            logger.error("Button 'כל הימים' not found — dumping page source for debug.")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
            raise

        scroll_down(driver)

        matches = []

        try:
            all_markets = driver.find_elements(By.CLASS_NAME, "MARKET_TYPE_HEADER")
            for market_index, market in enumerate(all_markets):
                try:
                    all_markets = driver.find_elements(By.CLASS_NAME, "MARKET_TYPE_HEADER")
                    market = all_markets[market_index]

                    game_type = safe_find(market, By.CLASS_NAME, "market-date-x")
                    item_leagues = market.find_elements(By.CLASS_NAME, "item-leagues")
                    current_date = None

                    for league_container in item_leagues:
                        try:
                            elements = league_container.find_elements(By.XPATH, "./div/div")
                            for i, elem in enumerate(elements):
                                try:
                                    class_attr = elem.get_attribute("class")
                                    if not class_attr:
                                        current_date = safe_find(elem, By.XPATH, "./div/span/span[3]", default=current_date)
                                    elif "LEAGUE_HEADER" in class_attr:
                                        league_header = elem.find_element(By.CLASS_NAME, "league-header")
                                        league_name = safe_find(league_header, By.TAG_NAME, 'span')
                                        game_container = elem.find_element(By.CLASS_NAME, "markets-container")
                                        games = game_container.find_elements(By.CLASS_NAME, "market")
                                        for game in games:
                                            game_time = safe_find(game, By.CLASS_NAME, 'time')
                                            odds = game.find_elements(By.CLASS_NAME, 'outcome')
                                            fulldate = current_date.split('.')
                                            formatted_date = f"{datetime.datetime.now().year}-{fulldate[1]}-{fulldate[0]}"
                                            match_data = [game_type, league_name, formatted_date, game_time]

                                            for odd in odds:
                                                try:
                                                    team_span = safe_find(odd, By.CLASS_NAME, 'hasHebrewCharacters')
                                                    if not team_span:
                                                        continue
                                                    ratio = safe_find(odd, By.CLASS_NAME, 'ratio')
                                                    team_name = get_team_name(team_span)
                                                    if len(match_data) < 8:
                                                        match_data += [team_name, ratio]
                                                except Exception as e:
                                                    logger.warning(f"Error processing odds: {e}")
                                                    continue

                                            if len(match_data) == 8:
                                                logger.info(f"Match found: {match_data}")
                                                matches.append(match_data)
                                            else:
                                                logger.warning(f"Incomplete match data: {match_data}")

                                except Exception as e:
                                    logger.warning(f"Error processing element at index {i}: {e}")
                                    continue

                        except StaleElementReferenceException:
                            logger.warning("StaleElementReferenceException caught — refreshing league container.")
                            continue

                except StaleElementReferenceException:
                    logger.warning("StaleElementReferenceException caught — refreshing market element.")
                    continue

        except Exception as e:
            logger.error(f"General error processing markets: {e}")

        driver.quit()
        columns = ["game_type", "league_name", "game_date", "game_time", 'Team1', "Outcome1", 'Team2', "Outcome2"]
        save_df_to_sql(columns, matches)
        last_date = get_db(command="SELECT max(game_date) from games;")
        return last_date[0][0]

    except Exception as e:
        logger.error(f"Error in activate_bot: {e}")
        driver.quit()
        raise
