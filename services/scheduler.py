import asyncio
import logging
from services.scraper_engine import run_scrapers
from config import SCRAPE_INTERVAL_HOURS

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self.scrape_loop())
        logger.info("Scheduler started")

    async def scrape_loop(self):
        while self.running:
            try:
                logger.info("Running scheduled scraping job")
                results = await run_scrapers()
                total_jobs = sum(results.values())
                logger.info(f"Scraping finished: {total_jobs} jobs added")
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(SCRAPE_INTERVAL_HOURS * 3600)


def setup_scheduler():
    return Scheduler()
