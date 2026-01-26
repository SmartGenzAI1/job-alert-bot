import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "secret123")

DB_FILE = "database.db"

TIMEZONE = "Asia/Kolkata"
SCRAPE_INTERVAL_HOURS = 3
DAILY_ALERT_HOUR = 9

SEND_BATCH_SIZE = 25
SEND_BATCH_SLEEP = 0.6
