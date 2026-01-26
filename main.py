from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from telegram import Update

from config import WEBHOOK_BASE_URL, WEBHOOK_TOKEN
from bot import create_bot
from database.db import init_db

app = FastAPI()
tg_app = create_bot()

init_db()


@app.on_event("startup")
async def startup():
    await tg_app.initialize()
    await tg_app.bot.set_webhook(f"{WEBHOOK_BASE_URL}/webhook/{WEBHOOK_TOKEN}")


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != WEBHOOK_TOKEN:
        return PlainTextResponse("Forbidden", 403)

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)

    return "ok"


@app.get("/")
def health():
    return {"status": "running"}
