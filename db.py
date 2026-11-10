"""Foydalanuvchilarni SQLite'da saqlash."""
import os

import aiosqlite

from cities import DEFAULT_CITY

DB_PATH = os.getenv("DB_PATH", "namoz.db")


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                city    TEXT NOT NULL DEFAULT ?,
                active  INTEGER NOT NULL DEFAULT 1
            )
            """.replace("?", f"'{DEFAULT_CITY}'")
        )
        await db.commit()


async def add_user(chat_id: int) -> None:
    """Yangi foydalanuvchi qo'shadi yoki qayta faollashtiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (chat_id) VALUES (?) "
            "ON CONFLICT(chat_id) DO UPDATE SET active = 1",
            (chat_id,),
        )
        await db.commit()


async def set_city(chat_id: int, city: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (chat_id, city) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET city = excluded.city, active = 1",
            (chat_id, city),
        )
        await db.commit()


async def get_city(chat_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT city FROM users WHERE chat_id = ?", (chat_id,)) as cur:
            row = await cur.fetchone()
    return row[0] if row else DEFAULT_CITY


async def deactivate_user(chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET active = 0 WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_active_users() -> list[tuple[int, str]]:
    """Faol foydalanuvchilar: [(chat_id, city), ...]"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id, city FROM users WHERE active = 1") as cur:
            return [(r[0], r[1]) for r in await cur.fetchall()]
