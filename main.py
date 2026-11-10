import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles

import db
from bot import bot, dp
from config import WEBAPP_URL, WEBHOOK_SECRET

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db.init_db()
        logging.info("Baza ulandi")
    except Exception:
        logging.exception("Baza ulanmadi (DATABASE_URL ni tekshiring)")

    if WEBAPP_URL:
        await bot.set_webhook(
            f"{WEBAPP_URL}/webhook",
            secret_token=WEBHOOK_SECRET or None,
            drop_pending_updates=True,
        )
        logging.info("Webhook o'rnatildi: %s/webhook", WEBAPP_URL)
    else:
        logging.warning("WEBAPP_URL yo'q, webhook o'rnatilmadi")

    yield

    await db.close_db()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


# Mini App sahifasi: /app/ manzilida ochiladi
app.mount("/app", StaticFiles(directory="webapp", html=True), name="webapp")
