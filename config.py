import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# --- Secrets ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "1234")

# --- Settings ---
RUN_INTERVAL_SECONDS = int(os.getenv("RUN_INTERVAL_SECONDS", "60"))

# --- Paths ---
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Ensure Core Directories Exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database & State Tracking
DB_PATH = DATA_DIR / "tracker.sqlite"
STATE_FILE_TELEMETRY = DATA_DIR / "telemetry_state.json"
STATE_FILE_NOTIFICATIONS = DATA_DIR / "sent_notifications.json"
AUTHORIZED_USERS_FILE = DATA_DIR / "authorized_users.txt"

# Team Mappings
NAME_MAPPINGS_FILE = DATA_DIR / "name_mappings.json"
PENDING_MAPPINGS_FILE = DATA_DIR / "pending_mappings.json"
UNIBET_TEAMS_MAP_FILE = DATA_DIR / "unibet_teams_map.json"

# League Configurations
UNIBET_LEAGUES_FILE = DATA_DIR / "unibet_leagues.json"
WINNER_TO_UNIBET_LEAGUES = BASE_DIR / "winner_to_unibet_leagues.json"
WINNER_TO_PINNACLE_LEAGUES = BASE_DIR / "winner_to_pinnacle_leagues.json"

# Logs and Reports
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
