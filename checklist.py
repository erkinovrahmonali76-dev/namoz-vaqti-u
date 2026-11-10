"""O'qilgan namozlarni belgilash (✅ ro'yxati)."""
import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

import db
from config import PRAYERS


async def init_log_table() -> None:
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prayer_log (
                chat_id INTEGER NOT NULL,
                day     TEXT    NOT NULL,
                prayer  TEXT    NOT NULL,
                PRIMARY KEY (chat_id, day, prayer)
            )
            """
        )
        await conn.commit()


async def get_done(chat_id: int, day: str) -> set[str]:
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute(
            "SELECT prayer FROM prayer_log WHERE chat_id = ? AND day = ?", (chat_id, day)
        ) as cur:
            return {r[0] for r in await cur.fetchall()}


async def toggle(chat_id: int, day: str, prayer: str) -> bool:
    """Belgini almashtiradi. Hozir belgilangan bo'lsa True qaytaradi."""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute(
            "SELECT 1 FROM prayer_log WHERE chat_id = ? AND day = ? AND prayer = ?",
            (chat_id, day, prayer),
        ) as cur:
            exists = await cur.fetchone() is not None
        if exists:
            await conn.execute(
                "DELETE FROM prayer_log WHERE chat_id = ? AND day = ? AND prayer = ?",
                (chat_id, day, prayer),
            )
        else:
            await conn.execute(
                "INSERT INTO prayer_log (chat_id, day, prayer) VALUES (?, ?, ?)",
                (chat_id, day, prayer),
            )
        await conn.commit()
    return not exists


async def build_checklist(chat_id: int, day: str, upto: int):
    """Shu kungi (upto indeksigacha bo'lgan) namozlar ro'yxati va tugmalari."""
    done = await get_done(chat_id, day)
    kb = InlineKeyboardBuilder()
    for i, name in enumerate(PRAYERS[: upto + 1]):
        mark = "✅" if name in done else "⬜"
        kb.add(InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"pr:{day}:{i}:{upto}"))
    kb.adjust(2)
    text = (
        "🤲 <b>Qaysi namozlarni o'qidingiz?</b>\n"
        "O'qiganlaringizni ✅ qilib belgilang:"
    )
    return text, kb.as_markup()
