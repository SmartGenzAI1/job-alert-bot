import asyncio
import logging
from typing import Dict
from .scrapers import SCRAPER_REGISTRY

logger = logging.getLogger(__name__)

async def run_scraper_async(name: str) -> int:
    try:
        scraper_class = SCRAPER_REGISTRY[name]
        scraper = scraper_class()
        jobs_added = await scraper.scrape()
        logger.info(f"{name} scraper added {jobs_added} jobs")
        return jobs_added
    except Exception as e:
        logger.error(f"{name} scraper failed: {e}")
        return 0


async def run_scrapers() -> Dict[str, int]:
    logger.info("Starting scraping job")

    results = {}
    tasks = []

    for name in SCRAPER_REGISTRY.keys():
        tasks.append(run_scraper_async(name))

    completed = await asyncio.gather(*tasks, return_exceptions=True)

    i = 0
    for name in SCRAPER_REGISTRY.keys():
        result = completed[i]
        if isinstance(result, Exception):
            logger.error(f"Scraper {name} failed: {result}")
            results[name] = 0
        else:
            results[name] = result
        i += 1

    total_jobs = sum(results.values())
    logger.info(f"Scraping completed: {total_jobs} total jobs added")

    return results
