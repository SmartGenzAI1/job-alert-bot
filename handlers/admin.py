from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database.models import get_users
from database.db import cur


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await update.message.reply_text(f"Users: {count}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = " ".join(context.args)
    for uid, _ in get_users():
        await context.bot.send_message(uid, text)
