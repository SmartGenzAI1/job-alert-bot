from telegram import Update
from telegram.ext import ContextTypes
from database.models import get_latest_jobs


async def send_jobs(update, typ):
    jobs = get_latest_jobs(typ)

    for t, c, l in jobs:
        await update.message.reply_text(f"📌 {t}\n🏢 {c}\n🔗 {l}")


async def jobs_cmd(u, c): await send_jobs(u, "jobs")
async def remote_cmd(u, c): await send_jobs(u, "remote")
async def internships_cmd(u, c): await send_jobs(u, "internships")
async def scholarships_cmd(u, c): await send_jobs(u, "scholarships")
