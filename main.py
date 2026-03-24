import logging
from fastapi import FastAPI
from services.scheduler import setup_scheduler
from services.scraper_engine import run_scrapers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
scheduler = setup_scheduler()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting bot...")

    await scheduler.start()

    # Run scraper immediately on startup
    await run_scrapers()

    logger.info("Startup scraping completed")


@app.get("/")
def home():
    return {"status": "Bot is running"}
