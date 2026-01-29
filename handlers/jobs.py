from telegram import Update
from telegram.ext import ContextTypes
from database.models import get_latest_jobs
from utils.logger import logger


async def send_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE, typ: str):
    """Send job listings for a specific type."""
    try:
        if not update.message:
            return

        # Get category name for display
        category_names = {
            "jobs": "Jobs",
            "remote": "Remote Work",
            "internships": "Internships", 
            "scholarships": "Scholarships"
        }
        category_display = category_names.get(typ, typ.title())

        # Get jobs from database
        jobs = get_latest_jobs(typ, limit=10)
        
        if not jobs:
            await update.message.reply_text(
                f"📭 No {category_display.lower()} found at the moment.\n"
                f"Please check back later or use /start to subscribe to daily alerts!"
            )
            return

        # Send jobs in batches to avoid message length limits
        for i, (title, company, link) in enumerate(jobs, 1):
            message = (
                f"📌 *{title}*\n"
                f"🏢 {company}\n"
                f"🔗 {link}\n"
                f"\n_{i}/{len(jobs)}_"
            )
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
            # Add small delay between messages to avoid rate limiting
            if i < len(jobs):
                import asyncio
                await asyncio.sleep(0.5)

        if update.effective_user:
            logger.info(f"Sent {len(jobs)} {typ} jobs to user {update.effective_user.id}")
        else:
            logger.info(f"Sent {len(jobs)} {typ} jobs to unknown user")

    except Exception as e:
        logger.error(f"Error sending {typ} jobs: {e}")
        if update.message:
            await update.message.reply_text(
                "❌ Sorry, there was an error retrieving job listings. Please try again later."
            )


async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /jobs command."""
    await send_jobs(update, context, "jobs")


async def remote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remote command."""
    await send_jobs(update, context, "remote")


async def internships_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /internships command."""
    await send_jobs(update, context, "internships")


async def scholarships_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scholarships command."""
    await send_jobs(update, context, "scholarships")
