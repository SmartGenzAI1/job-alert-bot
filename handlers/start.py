from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import ContextTypes
from database.models import add_user, set_category


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.full_name)

    keyboard = [
        [InlineKeyboardButton("Jobs", callback_data="jobs"),
         InlineKeyboardButton("Internships", callback_data="internships")],
        [InlineKeyboardButton("Remote", callback_data="remote"),
         InlineKeyboardButton("Scholarships", callback_data="scholarships")]
    ]

    await update.message.reply_text(
        "Choose your alerts:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    set_category(q.from_user.id, q.data)
    await q.edit_message_text(f"Subscribed to {q.data}")
