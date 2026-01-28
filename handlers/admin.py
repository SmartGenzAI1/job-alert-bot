from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID, logger
from database.models import get_users, get_user_count, get_job_count


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command for admin."""
    try:
        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not update.message:
            return

        # Get database statistics
        from database.db import get_db_stats
        stats = get_db_stats()
        
        if not stats:
            await update.message.reply_text("❌ Unable to retrieve statistics at this time.")
            return

        # Format statistics message
        message = (
            "📊 *Bot Statistics*\n\n"
            f"👥 *Users*: {stats.get('total_users', 0)}\n"
            f"💼 *Total Jobs*: {stats.get('total_jobs', 0)}\n"
            f"🆕 *Recent Jobs (24h)*: {stats.get('recent_jobs', 0)}\n\n"
            "*Jobs by Category:*\n"
        )
        
        jobs_by_type = stats.get('jobs_by_type', {})
        for job_type, count in jobs_by_type.items():
            category_names = {
                "jobs": "Jobs",
                "remote": "Remote",
                "internships": "Internships",
                "scholarships": "Scholarships"
            }
            display_name = category_names.get(job_type, job_type.title())
            message += f"  • {display_name}: {count}\n"

        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"Admin {ADMIN_ID} requested statistics")

    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        if update.message:
            await update.message.reply_text("❌ Error retrieving statistics. Please try again later.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command for admin."""
    try:
        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not update.message:
            return

        # Check if message text is provided
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /broadcast <message>\n"
                "Example: /broadcast Hello everyone! Check out new job listings."
            )
            return

        # Join the message arguments
        message_text = " ".join(context.args)
        
        # Validate message length
        if len(message_text) > 4000:  # Telegram message limit
            await update.message.reply_text(
                "❌ Message too long. Please keep it under 4000 characters."
            )
            return

        # Confirm broadcast
        await update.message.reply_text(
            f"📤 *Broadcast Preview:*\n\n{message_text}\n\n"
            f"Are you sure you want to send this to all users? "
            f"Use /confirm_broadcast to proceed.",
            parse_mode="Markdown"
        )
        
        # Store the message in context for confirmation
        if context.user_data is None:
            context.user_data = {}
        context.user_data['pending_broadcast'] = message_text
        logger.info(f"Admin {ADMIN_ID} prepared broadcast message")

    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        if update.message:
            await update.message.reply_text("❌ Error processing broadcast. Please try again later.")


async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send the broadcast message."""
    try:
        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not update.message:
            return

        # Check if there's a pending broadcast
        if not context.user_data or 'pending_broadcast' not in context.user_data:
            await update.message.reply_text(
                "❌ No pending broadcast message. Use /broadcast first."
            )
            return
        
        pending_message = context.user_data['pending_broadcast']
        if not pending_message:
            await update.message.reply_text(
                "❌ No pending broadcast message. Use /broadcast first."
            )
            return

        # Get all users
        users = get_users()
        if not users:
            await update.message.reply_text("❌ No users found to broadcast to.")
            return

        # Send broadcast message
        sent_count = 0
        failed_count = 0
        
        await update.message.reply_text(
            f"📤 Sending broadcast to {len(users)} users...",
            parse_mode="Markdown"
        )

        for user_id, _ in users:
            try:
                await context.bot.send_message(user_id, pending_message)
                sent_count += 1
                
                # Add small delay to avoid rate limiting
                import asyncio
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
                failed_count += 1

        # Clear pending message
        if context.user_data and 'pending_broadcast' in context.user_data:
            del context.user_data['pending_broadcast']

        # Send summary
        await update.message.reply_text(
            f"✅ Broadcast completed!\n"
            f"📤 Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}",
            parse_mode="Markdown"
        )
        
        logger.info(f"Admin {ADMIN_ID} sent broadcast to {sent_count} users ({failed_count} failed)")

    except Exception as e:
        logger.error(f"Error in confirm_broadcast: {e}")
        if update.message:
            await update.message.reply_text("❌ Error sending broadcast. Please try again later.")


async def cleanup_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cleanup_jobs command for admin."""
    try:
        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not update.message:
            return

        # Get days parameter (default 30)
        days = 30
        if context.args and context.args[0].isdigit():
            days = int(context.args[0])
            if days < 1 or days > 365:
                await update.message.reply_text("❌ Days must be between 1 and 365.")
                return

        # Confirm cleanup
        await update.message.reply_text(
            f"🧹 *Cleanup Confirmation*\n\n"
            f"This will delete all job listings older than {days} days.\n"
            f"Are you sure? Use /confirm_cleanup to proceed.",
            parse_mode="Markdown"
        )
        
        # Store days in context for confirmation
        if context.user_data is None:
            context.user_data = {}
        context.user_data['pending_cleanup_days'] = days
        logger.info(f"Admin {ADMIN_ID} prepared cleanup for {days} days")

    except Exception as e:
        logger.error(f"Error in cleanup_jobs command: {e}")
        if update.message:
            await update.message.reply_text("❌ Error processing cleanup. Please try again later.")


async def confirm_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute job cleanup."""
    try:
        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not update.message:
            return

        # Check if there's a pending cleanup
        if not context.user_data or 'pending_cleanup_days' not in context.user_data:
            await update.message.reply_text(
                "❌ No pending cleanup. Use /cleanup_jobs first."
            )
            return
        
        days = context.user_data['pending_cleanup_days']
        if days is None:
            await update.message.reply_text(
                "❌ No pending cleanup. Use /cleanup_jobs first."
            )
            return

        # Execute cleanup
        from database.models import cleanup_old_jobs
        
        deleted_count = cleanup_old_jobs(days)
        
        # Clear pending cleanup
        if context.user_data and 'pending_cleanup_days' in context.user_data:
            del context.user_data['pending_cleanup_days']

        # Send result
        await update.message.reply_text(
            f"🧹 Cleanup completed!\n"
            f"🗑️ Deleted {deleted_count} old job listings (older than {days} days).",
            parse_mode="Markdown"
        )
        
        logger.info(f"Admin {ADMIN_ID} cleaned up {deleted_count} old jobs")

    except Exception as e:
        logger.error(f"Error in confirm_cleanup: {e}")
        if update.message:
            await update.message.reply_text("❌ Error executing cleanup. Please try again later.")
