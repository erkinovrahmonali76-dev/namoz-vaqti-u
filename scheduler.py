"""Eslatmalar: namozga REMIND_BEFORE_MIN daqiqa qolganda va namoz vaqti kirganda."""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

import db
from config import NOTIFY_AT_TIME, REMIND_BEFORE_MIN, TIMEZONE
from prayer_times import get_prayer_times

CHECK_EVERY_SEC = 20
# Vaqt o'tib ketgan bo'lsa ham shu oynada hali yuboriladi (kechikishlarga chidamlilik)
GRACE_SEC = 90

_sent: set[tuple] = set()  # (chat_id, sana, namoz, tur)


def _due(now: datetime, target: datetime) -> bool:
    delta = (now - target).total_seconds()
    return 0 <= delta < GRACE_SEC


async def _send(bot: Bot, chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id, text)
    except TelegramForbiddenError:
        # Foydalanuvchi botni bloklagan
        await db.deactivate_user(chat_id)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id, text)
    except Exception:
        logging.exception("Xabar yuborishda xato (chat_id=%s)", chat_id)


async def _tick(bot: Bot) -> None:
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    by_city: dict[str, list[int]] = defaultdict(list)
    for chat_id, city in await db.get_active_users():
        by_city[city].append(chat_id)

    for city, chat_ids in by_city.items():
        try:
            times = await get_prayer_times(city, now.date())
        except Exception:
            logging.exception("Vaqtlarni olishda xato: %s", city)
            continue

        for prayer, t in times.items():
            events = [("before", t - timedelta(minutes=REMIND_BEFORE_MIN))]
            if NOTIFY_AT_TIME:
                events.append(("at", t))

            for kind, target in events:
                if not _due(now, target):
                    continue
                if kind == "before":
                    text = f"⏰ <b>{prayer}</b> namoziga {REMIND_BEFORE_MIN} daqiqa qoldi.\nVaqti: <b>{t.strftime('%H:%M')}</b> ({city})"
                else:
                    text = f"🕌 <b>{prayer}</b> namozi vaqti kirdi ({t.strftime('%H:%M')}, {city}).\nHayya alas-salah! 🤲"

                for chat_id in chat_ids:
                    key = (chat_id, now.date(), prayer, kind)
                    if key in _sent:
                        continue
                    _sent.add(key)
                    await _send(bot, chat_id, text)
                    await asyncio.sleep(0.05)  # Telegram limitlari uchun

    # Eski yozuvlarni tozalash
    for key in [k for k in _sent if k[1] < now.date()]:
        _sent.discard(key)


async def run_scheduler(bot: Bot) -> None:
    logging.info("Eslatma tizimi ishga tushdi")
    while True:
        try:
            await _tick(bot)
        except Exception:
            logging.exception("Scheduler xatosi")
        await asyncio.sleep(CHECK_EVERY_SEC)
