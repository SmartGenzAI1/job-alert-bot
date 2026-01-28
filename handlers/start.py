from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes
from database.models import add_user, set_category
from config import logger


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and user registration."""
    try:
        user = update.effective_user
        if not user:
            if update.message:
                await update.message.reply_text("Error: Unable to get user information.")
            return

        # Register user
        success = add_user(user.id, user.full_name)
        if success:
            logger.info(f"New user started bot: {user.id} - {user.full_name}")
        else:
            logger.debug(f"Existing user started bot: {user.id} - {user.full_name}")

        # Create category selection keyboard
        keyboard = [
            [InlineKeyboardButton("Jobs", callback_data="jobs"),
             InlineKeyboardButton("Internships", callback_data="internships")],
            [InlineKeyboardButton("Remote", callback_data="remote"),
             InlineKeyboardButton("Scholarships", callback_data="scholarships")]
        ]

        if update.message:
            await update.message.reply_text(
                "🎯 Welcome to Job Alert Bot!\n\n"
                "Choose the type of alerts you want to receive:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        if update.message:
            await update.message.reply_text("Sorry, there was an error. Please try again later.")


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection callback."""
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()

        # Validate callback data
        valid_categories = ["jobs", "remote", "internships", "scholarships"]
        if query.data not in valid_categories:
            await query.edit_message_text("❌ Invalid category selected.")
            return

        # Update user category
        success = set_category(query.from_user.id, query.data)
        if success:
            category_names = {
                "jobs": "Jobs",
                "remote": "Remote Work",
                "internships": "Internships", 
                "scholarships": "Scholarships"
            }
            category_display = category_names.get(query.data, query.data.title())
            
            await query.edit_message_text(
                f"✅ Successfully subscribed to **{category_display}** alerts!\n\n"
                f"🔔 You will receive daily updates at 9 AM IST.\n"
                f"Use /jobs, /remote, /internships, or /scholarships to see current listings.",
                parse_mode="Markdown"
            )
            logger.info(f"User {query.from_user.id} subscribed to {query.data}")
        else:
            await query.edit_message_text(
                "❌ Error updating your preferences. Please try again or contact support."
            )
            logger.warning(f"Failed to update category for user {query.from_user.id}")

    except Exception as e:
        logger.error(f"Error in category callback: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "❌ An error occurred. Please try again later."
            )
