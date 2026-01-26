from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

from config import SCRAPE_INTERVAL_HOURS, DAILY_ALERT_HOUR, TIMEZONE
from services.scraper_engine import run_scrapers
from services.notifier import notify_users
from database.models import get_users
from database.db import cur


def setup_scheduler(app):

    async def daily_alert(context):
        since = datetime.utcnow() - timedelta(days=1)
        users = get_users()

        for uid, cat in users:
            jobs = cur.execute(
                "SELECT title,company,link FROM jobs WHERE type=? AND created_at>=?",
                (cat, since)
            ).fetchall()

            await notify_users(context.bot, [(uid, cat)], jobs)

    app.job_queue.run_repeating(
        lambda c: run_scrapers(),
        interval=SCRAPE_INTERVAL_HOURS * 3600
    )

    app.job_queue.run_daily(
        daily_alert,
        time=ZoneInfo(TIMEZONE).fromutc(datetime.utcnow()).replace(
            hour=DAILY_ALERT_HOUR, minute=0, second=0
        ).timetz()
    )
