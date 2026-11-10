"""Mini App uchun API: e'lon berish, qidirish, band qilish."""
import html
import logging
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import db
from auth import current_user
from bot import bot
from config import REGIONS

router = APIRouter(prefix="/api")
TZ = ZoneInfo("Asia/Tashkent")

# Taqvimlar uchun bir xil apostrof
_APOS = re.compile(r"[‘’ʻʼ`´]")


def norm_place(value: str) -> str:
    value = _APOS.sub("'", value).strip()
    return re.sub(r"\s+", " ", value)


def norm_phone(value: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", value)
    if len(re.sub(r"\D", "", cleaned)) < 9:
        raise HTTPException(400, "Telefon raqamni to'g'ri kiriting")
    return cleaned


def fmt_dt(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%d.%m.%Y %H:%M")


async def notify(chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id, text)
    except Exception:
        logging.exception("Xabar yuborilmadi (chat_id=%s)", chat_id)


def pool():
    if db.pool is None:
        raise HTTPException(503, "Baza ulanmagan")
    return db.pool


# ---------- Modellar ----------
class RideIn(BaseModel):
    from_place: str = Field(min_length=2, max_length=40)
    to_place: str = Field(min_length=2, max_length=40)
    depart_at: str  # "YYYY-MM-DDTHH:MM" (Toshkent vaqti)
    seats: int = Field(ge=1, le=8)
    price: int = Field(ge=0, le=5_000_000)
    car: str = Field(default="", max_length=40)
    phone: str = Field(min_length=7, max_length=20)
    note: str = Field(default="", max_length=200)


class BookIn(BaseModel):
    seats: int = Field(default=1, ge=1, le=8)
    phone: str = Field(min_length=7, max_length=20)


def ride_dict(r, *, seats_left: int | None = None) -> dict:
    return {
        "id": r["id"],
        "from_place": r["from_place"],
        "to_place": r["to_place"],
        "depart_at": r["depart_at"].astimezone(TZ).isoformat(),
        "seats": r["seats"],
        "seats_left": seats_left if seats_left is not None else r["seats"],
        "price": r["price"],
        "car": r["car"],
        "note": r["note"],
        "status": r["status"],
        "driver_name": r.get("driver_name", "") if hasattr(r, "get") else r["driver_name"],
    }


# ---------- Ochiq ma'lumotlar ----------
@router.get("/places")
async def places():
    return {"regions": REGIONS}


@router.get("/rides")
async def search_rides(from_place: str = "", to_place: str = "", day: str = ""):
    p_from = norm_place(from_place) or None
    p_to = norm_place(to_place) or None
    p_day: date | None = None
    if day:
        try:
            p_day = date.fromisoformat(day)
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")

    async with pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT r.*, u.name AS driver_name,
                   r.seats - COALESCE(b.taken, 0) AS seats_left
            FROM rides r
            JOIN users u ON u.tg_id = r.driver_id
            LEFT JOIN (
                SELECT ride_id, SUM(seats) AS taken
                FROM bookings WHERE status = 'active' GROUP BY ride_id
            ) b ON b.ride_id = r.id
            WHERE r.status = 'open'
              AND r.depart_at > now()
              AND r.seats - COALESCE(b.taken, 0) > 0
              AND ($1::text IS NULL OR lower(r.from_place) = lower($1))
              AND ($2::text IS NULL OR lower(r.to_place) = lower($2))
              AND ($3::date IS NULL OR (r.depart_at AT TIME ZONE 'Asia/Tashkent')::date = $3)
            ORDER BY r.depart_at
            LIMIT 100
            """,
            p_from, p_to, p_day,
        )
    return [ride_dict(dict(r), seats_left=int(r["seats_left"])) for r in rows]


# ---------- Haydovchi ----------
@router.post("/rides")
async def create_ride(body: RideIn, user: dict = Depends(current_user)):
    from_place, to_place = norm_place(body.from_place), norm_place(body.to_place)
    if len(from_place) < 2 or len(to_place) < 2:
        raise HTTPException(400, "Joy nomini kiriting")
    if from_place.lower() == to_place.lower():
        raise HTTPException(400, "Qayerdan va qayerga bir xil bo'lishi mumkin emas")
    try:
        depart = datetime.strptime(body.depart_at, "%Y-%m-%dT%H:%M").replace(tzinfo=TZ)
    except ValueError:
        raise HTTPException(400, "Sana va vaqt noto'g'ri")
    if depart <= datetime.now(TZ):
        raise HTTPException(400, "Ketish vaqti o'tib ketgan")
    phone = norm_phone(body.phone)

    async with pool().acquire() as conn:
        ride_id = await conn.fetchval(
            """
            INSERT INTO rides (driver_id, from_place, to_place, depart_at, seats, price, car, phone, note)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
            """,
            user["id"], from_place, to_place, depart, body.seats, body.price,
            body.car.strip(), phone, body.note.strip(),
        )
        await conn.execute("UPDATE users SET phone = $2 WHERE tg_id = $1", user["id"], phone)
    return {"id": ride_id}


@router.get("/my/rides")
async def my_rides(user: dict = Depends(current_user)):
    async with pool().acquire() as conn:
        rides = await conn.fetch(
            """
            SELECT r.*, '' AS driver_name FROM rides r
            WHERE r.driver_id = $1 ORDER BY r.depart_at DESC LIMIT 50
            """,
            user["id"],
        )
        ids = [r["id"] for r in rides]
        bookings = await conn.fetch(
            """
            SELECT b.id, b.ride_id, b.seats, b.phone, u.name
            FROM bookings b JOIN users u ON u.tg_id = b.passenger_id
            WHERE b.status = 'active' AND b.ride_id = ANY($1::bigint[])
            ORDER BY b.created_at
            """,
            ids,
        )

    by_ride: dict[int, list] = {}
    for b in bookings:
        by_ride.setdefault(b["ride_id"], []).append(
            {"id": b["id"], "name": b["name"], "seats": b["seats"], "phone": b["phone"]}
        )

    result = []
    for r in rides:
        taken = sum(b["seats"] for b in by_ride.get(r["id"], []))
        d = ride_dict(dict(r), seats_left=r["seats"] - taken)
        d["passengers"] = by_ride.get(r["id"], [])
        result.append(d)
    return result


@router.post("/rides/{ride_id}/cancel")
async def cancel_ride(ride_id: int, user: dict = Depends(current_user)):
    async with pool().acquire() as conn:
        async with conn.transaction():
            ride = await conn.fetchrow(
                "SELECT * FROM rides WHERE id = $1 AND driver_id = $2 FOR UPDATE",
                ride_id, user["id"],
            )
            if not ride:
                raise HTTPException(404, "E'lon topilmadi")
            if ride["status"] != "open":
                raise HTTPException(400, "E'lon allaqachon yopilgan")
            await conn.execute("UPDATE rides SET status = 'cancelled' WHERE id = $1", ride_id)
            passengers = await conn.fetch(
                "UPDATE bookings SET status = 'cancelled' "
                "WHERE ride_id = $1 AND status = 'active' RETURNING passenger_id",
                ride_id,
            )

    for p in passengers:
        await notify(
            p["passenger_id"],
            f"⚠️ Haydovchi safarni bekor qildi:\n"
            f"{html.escape(ride['from_place'])} → {html.escape(ride['to_place'])}, {fmt_dt(ride['depart_at'])}",
        )
    return {"ok": True}


# ---------- Yo'lovchi ----------
@router.post("/rides/{ride_id}/book")
async def book_ride(ride_id: int, body: BookIn, user: dict = Depends(current_user)):
    phone = norm_phone(body.phone)

    async with pool().acquire() as conn:
        async with conn.transaction():
            ride = await conn.fetchrow("SELECT * FROM rides WHERE id = $1 FOR UPDATE", ride_id)
            if not ride or ride["status"] != "open":
                raise HTTPException(404, "E'lon topilmadi yoki yopilgan")
            if ride["depart_at"] <= datetime.now(TZ):
                raise HTTPException(400, "Bu safar vaqti o'tib ketgan")
            if ride["driver_id"] == user["id"]:
                raise HTTPException(400, "O'z e'loningizni band qila olmaysiz")

            already = await conn.fetchval(
                "SELECT 1 FROM bookings WHERE ride_id = $1 AND passenger_id = $2 AND status = 'active'",
                ride_id, user["id"],
            )
            if already:
                raise HTTPException(400, "Siz bu safarni allaqachon band qilgansiz")

            taken = await conn.fetchval(
                "SELECT COALESCE(SUM(seats), 0) FROM bookings WHERE ride_id = $1 AND status = 'active'",
                ride_id,
            )
            if ride["seats"] - taken < body.seats:
                raise HTTPException(400, f"Bo'sh joy yetarli emas (qolgan: {ride['seats'] - taken})")

            booking_id = await conn.fetchval(
                "INSERT INTO bookings (ride_id, passenger_id, seats, phone) VALUES ($1, $2, $3, $4) RETURNING id",
                ride_id, user["id"], body.seats, phone,
            )
            await conn.execute("UPDATE users SET phone = $2 WHERE tg_id = $1", user["id"], phone)

    await notify(
        ride["driver_id"],
        f"🚗 <b>Yangi bron!</b>\n"
        f"{html.escape(ride['from_place'])} → {html.escape(ride['to_place'])}, {fmt_dt(ride['depart_at'])}\n\n"
        f"👤 {html.escape(user['name'])}\n"
        f"📞 {html.escape(phone)}\n"
        f"💺 Joy soni: {body.seats}",
    )
    return {"id": booking_id, "driver_phone": ride["phone"]}


@router.get("/my/bookings")
async def my_bookings(user: dict = Depends(current_user)):
    async with pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT b.id AS booking_id, b.seats AS booked_seats, b.status AS booking_status,
                   r.*, u.name AS driver_name, r.phone AS driver_phone
            FROM bookings b
            JOIN rides r ON r.id = b.ride_id
            JOIN users u ON u.tg_id = r.driver_id
            WHERE b.passenger_id = $1
            ORDER BY r.depart_at DESC LIMIT 50
            """,
            user["id"],
        )
    result = []
    for r in rows:
        d = ride_dict(dict(r))
        d.update(
            booking_id=r["booking_id"],
            booked_seats=r["booked_seats"],
            booking_status=r["booking_status"],
            driver_phone=r["driver_phone"],
        )
        result.append(d)
    return result


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, user: dict = Depends(current_user)):
    async with pool().acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE bookings SET status = 'cancelled'
            WHERE id = $1 AND passenger_id = $2 AND status = 'active'
            RETURNING ride_id, seats
            """,
            booking_id, user["id"],
        )
        if not row:
            raise HTTPException(404, "Bron topilmadi")
        ride = await conn.fetchrow("SELECT * FROM rides WHERE id = $1", row["ride_id"])

    if ride:
        await notify(
            ride["driver_id"],
            f"❌ Bron bekor qilindi:\n"
            f"{html.escape(ride['from_place'])} → {html.escape(ride['to_place'])}, {fmt_dt(ride['depart_at'])}\n"
            f"👤 {html.escape(user['name'])}, joy: {row['seats']}",
        )
    return {"ok": True}
