from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import TOKEN
from handlers.start import start, category_callback
from handlers.jobs import jobs_cmd, remote_cmd, internships_cmd, scholarships_cmd
from handlers.admin import stats, broadcast, confirm_broadcast, cleanup_jobs, confirm_cleanup
from services.scheduler import setup_scheduler
from utils.logger import logger


def create_bot():
    """Create and configure the Telegram bot application."""
    try:
        # Build application with job queue enabled
        app = (
            ApplicationBuilder()
            .token(TOKEN)
            .build()
        )
        
        logger.info("Bot application created successfully")

        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(category_callback))
        app.add_handler(CommandHandler("jobs", jobs_cmd))
        app.add_handler(CommandHandler("remote", remote_cmd))
        app.add_handler(CommandHandler("internships", internships_cmd))
        app.add_handler(CommandHandler("scholarships", scholarships_cmd))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("broadcast", broadcast))
        app.add_handler(CommandHandler("confirm_broadcast", confirm_broadcast))
        app.add_handler(CommandHandler("cleanup_jobs", cleanup_jobs))
        app.add_handler(CommandHandler("confirm_cleanup", confirm_cleanup))

        return app
        
    except Exception as e:
        logger.error(f"Failed to create bot: {e}")
        raise
