import requests
from database.models import add_job
from utils.logger import logger


def scrape_remoteok():
    url = "https://remoteok.com/remote-jobs.json"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        for item in data[1:40]:
            add_job(
                item.get("position"),
                item.get("company"),
                item.get("url"),
                "remote"
            )

    except Exception as e:
        logger.error(e)


def run_scrapers():
    logger.info("Running scrapers...")
    scrape_remoteok()
