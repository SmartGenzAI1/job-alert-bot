from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
import logging

from config import SCRAPE_INTERVAL_HOURS, DAILY_ALERT_HOUR, TIMEZONE, logger
from services.scraper_engine import run_scrapers
from services.notifier import notify_users
from database.models import get_users, get_db_connection


def setup_scheduler(app):
    """Set up the job scheduler for the bot."""
    
    async def daily_alert(context):
        """Send daily job alerts to all users."""
        try:
            logger.info("Starting daily alert job")
            
            # Get users from database
            users = get_users()
            if not users:
                logger.info("No users found for daily alerts")
                return

            logger.info(f"Sending daily alerts to {len(users)} users")
            
            # Process users in batches to avoid overwhelming the system
            batch_size = 50
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                await process_daily_alert_batch(context.bot, batch)
                
                # Small delay between batches to avoid rate limiting
                import asyncio
                if i + batch_size < len(users):
                    await asyncio.sleep(2)

            logger.info("Daily alert job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in daily alert job: {e}")

    async def process_daily_alert_batch(bot, user_batch):
        """Process a batch of users for daily alerts."""
        try:
            # Get jobs for each user's category
            since = datetime.utcnow() - timedelta(days=1)
            
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                for uid, cat in user_batch:
                    try:
                        # Get jobs for this user's category from the last 24 hours
                        jobs = cur.execute(
                            "SELECT title,company,link FROM jobs WHERE type=? AND created_at>=?",
                            (cat, since.isoformat())
                        ).fetchall()

                        if jobs:
                            await notify_users(bot, [(uid, cat)], jobs)
                        else:
                            logger.debug(f"No new jobs for user {uid} in category {cat}")
                            
                    except Exception as e:
                        logger.error(f"Error processing alert for user {uid}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error processing daily alert batch: {e}")

    async def scrape_and_notify(context):
        """Run scrapers and handle any errors."""
        try:
            logger.info("Starting scheduled scraping job")
            # Import here to avoid circular imports
            from services.scraper_engine import run_scrapers
            results = run_scrapers()
            total_jobs = sum(results.values())
            logger.info(f"Scheduled scraping job completed successfully: {total_jobs} jobs added")
            
        except Exception as e:
            logger.error(f"Error in scheduled scraping job: {e}")

    # Schedule scraping job
    app.job_queue.run_repeating(
        lambda context: app.application.create_task(scrape_and_notify(context)),
        interval=SCRAPE_INTERVAL_HOURS * 3600,
        name="scraping_job"
    )

    # Schedule daily alert job
    app.job_queue.run_daily(
        daily_alert,
        time=ZoneInfo(TIMEZONE).fromutc(datetime.utcnow()).replace(
            hour=DAILY_ALERT_HOUR, minute=0, second=0
        ).timetz(),
        name="daily_alert_job"
    )

    logger.info(f"Scheduled jobs configured: scraping every {SCRAPE_INTERVAL_HOURS} hours, daily alerts at {DAILY_ALERT_HOUR}:00 {TIMEZONE}")
