"""Telegram Mini App foydalanuvchisini tekshirish (initData imzosi + kanalga obuna)."""
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

import db
from bot import bot
from config import BOT_TOKEN, CHANNEL

MAX_AGE_SEC = 24 * 3600
_sub_ok: dict[int, float] = {}  # obuna bo'lganlar keshi (60 soniya)


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


async def is_subscribed(user_id: int) -> bool:
    """Foydalanuvchi kanal a'zosimi? (bot kanalda admin bo'lishi kerak)"""
    if time.time() - _sub_ok.get(user_id, 0) < 60:
        return True
    try:
        m = await bot.get_chat_member(CHANNEL, user_id)
        ok = m.status in ("member", "administrator", "creator")
    except Exception:
        logging.exception("Obunani tekshirib bo'lmadi. Bot kanalda admin ekanini tekshiring")
        return False
    if ok:
        _sub_ok[user_id] = time.time()
    return ok


async def current_user(x_init_data: str = Header(default="")) -> dict:
    """Har bir so'rovda foydalanuvchini aniqlaydi, obunani tekshiradi va bazaga yozadi."""
    if not x_init_data:
        raise HTTPException(401, "Ilovani Telegram ichidan oching")
    tg = validate_init_data(x_init_data)
    if db.pool is None:
        raise HTTPException(503, "Baza ulanmagan")

    if not await is_subscribed(tg["id"]):
        raise HTTPException(403, "not_subscribed")

    name = f"{tg.get('first_name', '')} {tg.get('last_name', '')}".strip()
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (tg_id, name) VALUES ($1, $2) "
            "ON CONFLICT (tg_id) DO UPDATE SET name = EXCLUDED.name",
            tg["id"], name,
        )
    return {"id": tg["id"], "name": name}
