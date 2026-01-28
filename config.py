import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_vars = ["TELEGRAM_TOKEN", "ADMIN_ID", "WEBHOOK_BASE_URL", "WEBHOOK_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please check your .env file or environment configuration.")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Telegram Configuration
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN is required but not set")
    raise ValueError("TELEGRAM_TOKEN is required but not set")

try:
    admin_id_str = os.getenv("ADMIN_ID")
    if not admin_id_str:
        logger.error("ADMIN_ID is required but not set")
        raise ValueError("ADMIN_ID is required but not set")
    ADMIN_ID = int(admin_id_str)
except ValueError:
    logger.error("ADMIN_ID must be a valid integer")
    raise ValueError("ADMIN_ID must be a valid integer")

# Webhook Configuration
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")
if not WEBHOOK_BASE_URL:
    logger.error("WEBHOOK_BASE_URL is required but not set")
    raise ValueError("WEBHOOK_BASE_URL is required but not set")
WEBHOOK_BASE_URL = WEBHOOK_BASE_URL.rstrip('/')
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")
if not WEBHOOK_TOKEN:
    logger.error("WEBHOOK_TOKEN is required but not set")
    raise ValueError("WEBHOOK_TOKEN is required but not set")

# Database Configuration
DB_FILE = os.getenv("DB_FILE", "database.db")

# Scheduling Configuration
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
try:
    SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "3"))
    DAILY_ALERT_HOUR = int(os.getenv("DAILY_ALERT_HOUR", "9"))
except ValueError:
    logger.error("SCRAPE_INTERVAL_HOURS and DAILY_ALERT_HOUR must be valid integers")
    raise ValueError("SCRAPE_INTERVAL_HOURS and DAILY_ALERT_HOUR must be valid integers")

# Messaging Configuration
try:
    SEND_BATCH_SIZE = int(os.getenv("SEND_BATCH_SIZE", "25"))
    SEND_BATCH_SLEEP = float(os.getenv("SEND_BATCH_SLEEP", "0.6"))
except ValueError:
    logger.error("SEND_BATCH_SIZE must be an integer and SEND_BATCH_SLEEP must be a float")
    raise ValueError("SEND_BATCH_SIZE must be an integer and SEND_BATCH_SLEEP must be a float")

# External Services Configuration
REMOTEOK_API_KEY = os.getenv("REMOTEOK_API_KEY", "")

logger.info("Configuration loaded successfully")
