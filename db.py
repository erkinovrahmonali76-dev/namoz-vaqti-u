"""PostgreSQL bazasi: ulanish va jadvallar."""
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import asyncpg

from config import DATABASE_URL

pool: asyncpg.Pool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id      BIGINT PRIMARY KEY,
    name       TEXT NOT NULL DEFAULT '',
    phone      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rides (
    id          BIGSERIAL PRIMARY KEY,
    driver_id   BIGINT NOT NULL REFERENCES users(tg_id),
    from_place  TEXT NOT NULL,
    to_place    TEXT NOT NULL,
    depart_at   TIMESTAMPTZ NOT NULL,
    seats       INTEGER NOT NULL CHECK (seats BETWEEN 1 AND 8),
    price       INTEGER NOT NULL CHECK (price >= 0),
    car         TEXT NOT NULL DEFAULT '',
    phone       TEXT NOT NULL,
    note        TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'open',   -- open | closed | cancelled
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rides_search
    ON rides (status, depart_at, lower(from_place), lower(to_place));

CREATE TABLE IF NOT EXISTS bookings (
    id            BIGSERIAL PRIMARY KEY,
    ride_id       BIGINT NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    passenger_id  BIGINT NOT NULL REFERENCES users(tg_id),
    seats         INTEGER NOT NULL CHECK (seats BETWEEN 1 AND 8),
    status        TEXT NOT NULL DEFAULT 'active',  -- active | cancelled
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bookings_ride ON bookings (ride_id);
CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings (passenger_id);
"""


def _clean_dsn(dsn: str) -> str:
    """Neon ba'zan asyncpg tushunmaydigan channel_binding parametrini qo'shadi - olib tashlaymiz."""
    parts = urlparse(dsn)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunparse(parts._replace(query=urlencode(query)))


async def init_db() -> None:
    global pool
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL topilmadi. .env yoki Render sozlamalarini tekshiring.")
    pool = await asyncpg.create_pool(_clean_dsn(DATABASE_URL), min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)


async def close_db() -> None:
    if pool:
        await pool.close()
