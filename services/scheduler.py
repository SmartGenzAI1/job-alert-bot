from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
import asyncio
import logging

from telegram.ext import Application

try:
    from telegram.ext import JobQueue
    JOBQUEUE_AVAILABLE = True
except ImportError:
    JOBQUEUE_AVAILABLE = False

from config import SCRAPE_INTERVAL_HOURS, DAILY_ALERT_HOUR, TIMEZONE
from utils.logger import logger
from services.scraper_engine import run_scrapers
from services.notifier import notify_users
from database.models import get_users, get_db_connection


class SchedulerManager:
    """Manages scheduled jobs for the bot with fallback mechanisms."""
    
    def __init__(self, app: Application):
        self.app = app
        self.job_queue = getattr(app, 'job_queue', None)
        self._fallback_tasks = []
        self._is_running = False
        
    async def start(self):
        """Start the scheduler with available mechanism."""
        if self.job_queue and JOBQUEUE_AVAILABLE:
            logger.info("Using PTB JobQueue for scheduling")
            self._setup_ptb_scheduler()
        else:
            logger.warning("PTB JobQueue not available, using fallback asyncio scheduler")
            await self._setup_fallback_scheduler()
        self._is_running = True
        
    async def stop(self):
        """Stop all scheduled tasks."""
        self._is_running = False
        for task in self._fallback_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._fallback_tasks.clear()
        logger.info("Scheduler stopped")
        
    def _setup_ptb_scheduler(self):
        """Set up scheduler using python-telegram-bot's JobQueue."""
        try:
            if not self.job_queue:
                logger.error("JobQueue is None, cannot setup PTB scheduler")
                raise RuntimeError("JobQueue not available")
                
            # Schedule scraping job
            self.job_queue.run_repeating(
                self._scrape_callback,
                interval=timedelta(hours=SCRAPE_INTERVAL_HOURS),
                name="scraping_job",
                first=10  # Start after 10 seconds
            )
            
            # Schedule daily alert job
            now = datetime.now(ZoneInfo(TIMEZONE))
            target_time = now.replace(hour=DAILY_ALERT_HOUR, minute=0, second=0, microsecond=0)
            if target_time <= now:
                target_time += timedelta(days=1)
            
            self.job_queue.run_daily(
                self._daily_alert_callback,
                time=target_time.timetz(),
                name="daily_alert_job"
            )
            
            logger.info(f"PTB Scheduler configured: scraping every {SCRAPE_INTERVAL_HOURS} hours, daily alerts at {DAILY_ALERT_HOUR}:00 {TIMEZONE}")
        except Exception as e:
            logger.error(f"Error setting up PTB scheduler: {e}")
            raise
            
    async def _setup_fallback_scheduler(self):
        """Set up fallback asyncio-based scheduler."""
        # Start scraping task
        scrape_task = asyncio.create_task(self._fallback_scrape_loop())
        self._fallback_tasks.append(scrape_task)
        
        # Start daily alert task
        alert_task = asyncio.create_task(self._fallback_daily_alert_loop())
        self._fallback_tasks.append(alert_task)
        
        logger.info(f"Fallback scheduler configured: scraping every {SCRAPE_INTERVAL_HOURS} hours, daily alerts at {DAILY_ALERT_HOUR}:00 {TIMEZONE}")
        
    async def _fallback_scrape_loop(self):
        """Fallback scraping loop using asyncio."""
        # Initial delay
        await asyncio.sleep(10)
        
        while self._is_running:
            try:
                await self._run_scrape_job()
            except Exception as e:
                logger.error(f"Error in fallback scrape loop: {e}")
            
            # Wait for next interval
            await asyncio.sleep(SCRAPE_INTERVAL_HOURS * 3600)
            
    async def _fallback_daily_alert_loop(self):
        """Fallback daily alert loop using asyncio."""
        while self._is_running:
            try:
                now = datetime.now(ZoneInfo(TIMEZONE))
                target_time = now.replace(hour=DAILY_ALERT_HOUR, minute=0, second=0, microsecond=0)
                
                if target_time <= now:
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.debug(f"Next daily alert in {wait_seconds} seconds")
                
                await asyncio.sleep(wait_seconds)
                
                if self._is_running:
                    await self._run_daily_alert_job()
                    
            except Exception as e:
                logger.error(f"Error in fallback daily alert loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
                
    async def _scrape_callback(self, context):
        """Callback for PTB JobQueue scraping job."""
        await self._run_scrape_job()
        
    async def _daily_alert_callback(self, context):
        """Callback for PTB JobQueue daily alert job."""
        await self._run_daily_alert_job()
        
    async def _run_scrape_job(self):
        """Run the scraping job."""
        try:
            logger.info("Starting scheduled scraping job")
            results = run_scrapers()
            total_jobs = sum(results.values())
            logger.info(f"Scheduled scraping job completed: {total_jobs} jobs added from {results}")
        except Exception as e:
            logger.error(f"Error in scheduled scraping job: {e}")
            
    async def _run_daily_alert_job(self):
        """Run the daily alert job."""
        try:
            logger.info("Starting daily alert job")
            
            users = get_users()
            if not users:
                logger.info("No users found for daily alerts")
                return
            
            logger.info(f"Sending daily alerts to {len(users)} users")
            
            # Process users in batches
            batch_size = 50
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                await self._process_daily_alert_batch(batch)
                
                if i + batch_size < len(users):
                    await asyncio.sleep(2)
                    
            logger.info("Daily alert job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in daily alert job: {e}")
            
    async def _process_daily_alert_batch(self, user_batch):
        """Process a batch of users for daily alerts."""
        try:
            since = datetime.utcnow() - timedelta(days=1)
            
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                for uid, cat in user_batch:
                    try:
                        jobs = cur.execute(
                            "SELECT title, company, link FROM jobs WHERE type=? AND created_at>=?",
                            (cat, since.isoformat())
                        ).fetchall()
                        
                        if jobs:
                            bot = self.app.bot
                            await notify_users(bot, [(uid, cat)], jobs)
                        else:
                            logger.debug(f"No new jobs for user {uid} in category {cat}")
                            
                    except Exception as e:
                        logger.error(f"Error processing alert for user {uid}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error processing daily alert batch: {e}")


def setup_scheduler(app: Application) -> SchedulerManager:
    """
    Set up the job scheduler for the bot.
    
    Args:
        app: The PTB Application instance
        
    Returns:
        SchedulerManager instance
    """
    scheduler = SchedulerManager(app)
    return scheduler
