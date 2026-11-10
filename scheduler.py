"""Eslatmalar: namozga oldin, namoz vaqti kirganda va namoz tugagach (✅ so'rovi)."""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

import db
from checklist import build_checklist
from config import NOTIFY_AT_TIME, PRAYERS, REMIND_BEFORE_MIN, TIMEZONE
from prayer_times import get_end_times, get_prayer_times

CHECK_EVERY_SEC = 20
GRACE_SEC = 90

_sent: set[tuple] = set()  # (chat_id, sana, namoz, tur)


def _due(now: datetime, target: datetime) -> bool:
    delta = (now - target).total_seconds()
    return 0 <= delta < GRACE_SEC


async def _send(bot: Bot, chat_id: int, text: str, markup=None) -> None:
    try:
        await bot.send_message(chat_id, text, reply_markup=markup)
    except TelegramForbiddenError:
        await db.deactivate_user(chat_id)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id, text, reply_markup=markup)
    except Exception:
        logging.exception("Xabar yuborishda xato (chat_id=%s)", chat_id)


async def _tick(bot: Bot) -> None:
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    day_str = now.date().isoformat()

    by_city: dict[str, list[int]] = defaultdict(list)
    for chat_id, city in await db.get_active_users():
        by_city[city].append(chat_id)

    for city, chat_ids in by_city.items():
        try:
            times = await get_prayer_times(city, now.date())
            ends = await get_end_times(city, now.date())
        except Exception:
            logging.exception("Vaqtlarni olishda xato: %s", city)
            continue

        for idx, prayer in enumerate(PRAYERS):
            t = times[prayer]
            events = [("before", t - timedelta(minutes=REMIND_BEFORE_MIN))]
            if NOTIFY_AT_TIME:
                events.append(("at", t))
            events.append(("end", ends[prayer]))

            for kind, target in events:
                if not _due(now, target):
                    continue

                for chat_id in chat_ids:
                    key = (chat_id, now.date(), prayer, kind)
                    if key in _sent:
                        continue
                    _sent.add(key)

                    if kind == "before":
                        await _send(
                            bot, chat_id,
                            f"⏰ <b>{prayer}</b> namoziga {REMIND_BEFORE_MIN} daqiqa qoldi.\n"
                            f"Vaqti: <b>{t.strftime('%H:%M')}</b> ({city})",
                        )
                    elif kind == "at":
                        await _send(
                            bot, chat_id,
                            f"🕌 <b>{prayer}</b> namozi vaqti kirdi ({t.strftime('%H:%M')}, {city}).\n"
                            "Hayya alas-salah! 🤲",
                        )
                    else:
                        text, markup = await build_checklist(chat_id, day_str, idx)
                        await _send(bot, chat_id, text, markup)
                    await asyncio.sleep(0.05)

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
