from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import TOKEN
from handlers.start import start, category_callback
from handlers.jobs import jobs_cmd, remote_cmd, internships_cmd, scholarships_cmd
from handlers.admin import stats, broadcast
from services.scheduler import setup_scheduler


def create_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_callback))
    app.add_handler(CommandHandler("jobs", jobs_cmd))
    app.add_handler(CommandHandler("remote", remote_cmd))
    app.add_handler(CommandHandler("internships", internships_cmd))
    app.add_handler(CommandHandler("scholarships", scholarships_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    setup_scheduler(app)

    return app
