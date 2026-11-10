"""Telegram Mini App foydalanuvchisini tekshirish (initData imzosi) va kanal obunasi."""
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

from aiogram.exceptions import TelegramAPIError
from fastapi import Depends, Header, HTTPException

import db
from bot import bot
from config import BOT_TOKEN, CHANNEL

MAX_AGE_SEC = 24 * 3600
SUB_TTL_SEC = 120

# Obuna bo'lganlar qisqa muddat eslab qolinadi (Telegram'ga ortiqcha so'rov bormasligi uchun)
_sub_cache: dict[int, float] = {}


def validate_init_data(init_data: str) -> dict:
    """Telegram bergan initData haqiqiyligini tekshiradi va user ma'lumotini qaytaradi."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        raise HTTPException(401, "Noto'g'ri ma'lumot")

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Imzo topilmadi")

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(401, "Imzo noto'g'ri")

    try:
        if time.time() - int(pairs.get("auth_date", "0")) > MAX_AGE_SEC:
            raise HTTPException(401, "Sessiya eskirgan, ilovani qayta oching")
        return json.loads(pairs["user"])
    except (KeyError, ValueError):
        raise HTTPException(401, "Foydalanuvchi topilmadi")


async def current_user(x_init_data: str = Header(default="")) -> dict:
    """Har bir so'rovda foydalanuvchini aniqlaydi va bazaga yozib qo'yadi."""
    if not x_init_data:
        raise HTTPException(401, "Ilovani Telegram ichidan oching")
    tg = validate_init_data(x_init_data)
    if db.pool is None:
        raise HTTPException(503, "Baza ulanmagan")

    name = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip()
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (tg_id, name) VALUES ($1, $2) "
            "ON CONFLICT (tg_id) DO UPDATE SET name = EXCLUDED.name",
            tg["id"], name,
        )
    return {"id": tg["id"], "name": name}


async def is_subscribed(user_id: int) -> bool:
    """Foydalanuvchi kanalga a'zomi? Kanal ko'rsatilmagan bo'lsa, tekshiruv o'chiq."""
    if not CHANNEL:
        return True
    now = time.time()
    if _sub_cache.get(user_id, 0) > now:
        return True
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
    except TelegramAPIError:
        # Bot kanalda admin bo'lmasa shu xato chiqadi. Hamma qulflanib qolmasligi uchun o'tkazib yuboramiz.
        logging.exception("Kanal a'zoligini tekshirib bo'lmadi (bot %s kanalida adminmi?)", CHANNEL)
        return True

    ok = member.status in ("creator", "administrator", "member") or (
        member.status == "restricted" and getattr(member, "is_member", False)
    )
    if ok:
        _sub_cache[user_id] = now + SUB_TTL_SEC
    return ok


async def subscribed_user(user: dict = Depends(current_user)) -> dict:
    """Kanalga obuna bo'lmagan foydalanuvchini to'xtatadi."""
    if not await is_subscribed(user["id"]):
        raise HTTPException(403, "subscribe_required")
    return user
