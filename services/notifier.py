import asyncio
from config import SEND_BATCH_SIZE, SEND_BATCH_SLEEP


async def notify_users(bot, users, jobs):
    batch = []

    for uid, _ in users:
        for t, c, l in jobs:
            msg = f"📌 {t}\n🏢 {c}\n🔗 {l}"
            batch.append(bot.send_message(uid, msg))

            if len(batch) >= SEND_BATCH_SIZE:
                await asyncio.gather(*batch, return_exceptions=True)
                batch.clear()
                await asyncio.sleep(SEND_BATCH_SLEEP)

    if batch:
        await asyncio.gather(*batch, return_exceptions=True)
