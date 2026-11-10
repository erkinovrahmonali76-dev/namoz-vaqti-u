"""Namoz vaqtlarini olish (Aladhan API, bepul, kalit talab qilmaydi)."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp

from cities import CITIES, DEFAULT_CITY
from config import TIMEZONE

API_URL = "https://api.aladhan.com/v1/timings/{d}"

API_TO_UZ = {
    "Fajr": "Bomdod",
    "Dhuhr": "Peshin",
    "Asr": "Asr",
    "Maghrib": "Shom",
    "Isha": "Xufton",
}

# method=3 (Muslim World League), school=1 (Hanafiy mazhabi, Asr uchun)
PARAMS = {"method": 3, "school": 1}

_cache: dict[tuple[str, date], tuple[dict[str, datetime], datetime]] = {}


def _parse(day: date, value: str, tz: ZoneInfo) -> datetime:
    hh, mm = value.split(" ")[0].split(":")
    return datetime(day.year, day.month, day.day, int(hh), int(mm), tzinfo=tz)


async def _load(city: str, day: date | None):
    if city not in CITIES:
        city = DEFAULT_CITY
    tz = ZoneInfo(TIMEZONE)
    day = day or datetime.now(tz).date()

    key = (city, day)
    if key in _cache:
        return _cache[key]

    lat, lon = CITIES[city]
    params = {**PARAMS, "latitude": lat, "longitude": lon, "timezonestring": TIMEZONE}
    url = API_URL.format(d=day.strftime("%d-%m-%Y"))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    timings = data["data"]["timings"]
    times = {uz: _parse(day, timings[api], tz) for api, uz in API_TO_UZ.items()}
    sunrise = _parse(day, timings["Sunrise"], tz)

    for k in [k for k in _cache if k[1] < day]:
        del _cache[k]
    _cache[key] = (times, sunrise)
    return _cache[key]


async def get_prayer_times(city: str = DEFAULT_CITY, day: date | None = None) -> dict[str, datetime]:
    """5 mahal namoz boshlanish vaqti: {"Bomdod": datetime, ...}"""
    times, _ = await _load(city, day)
    return times


async def get_end_times(city: str = DEFAULT_CITY, day: date | None = None) -> dict[str, datetime]:
    """Har bir namoz vaqti tugash payti.

    Bomdod - quyosh chiqishi, Peshin - Asr boshlanishi, Asr - Shom boshlanishi,
    Shom - Xufton boshlanishi, Xufton - 2 soat keyin (ko'pi bilan 23:30).
    """
    times, sunrise = await _load(city, day)
    xufton_end = min(
        times["Xufton"] + timedelta(hours=2),
        times["Xufton"].replace(hour=23, minute=30),
    )
    return {
        "Bomdod": sunrise,
        "Peshin": times["Asr"],
        "Asr": times["Shom"],
        "Shom": times["Xufton"],
        "Xufton": xufton_end,
    }
