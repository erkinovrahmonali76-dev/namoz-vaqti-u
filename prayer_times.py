"""Namoz vaqtlarini olish (Aladhan API, bepul, kalit talab qilmaydi)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import aiohttp

from cities import CITIES, DEFAULT_CITY
from config import TIMEZONE

API_URL = "https://api.aladhan.com/v1/timings/{d}"

# Aladhan kalitlari -> o'zbekcha nomlar (tartib muhim)
API_TO_UZ = {
    "Fajr": "Bomdod",
    "Dhuhr": "Peshin",
    "Asr": "Asr",
    "Maghrib": "Shom",
    "Isha": "Xufton",
}

# method=3 (Muslim World League), school=1 (Hanafiy mazhabi, Asr uchun)
# Eslatma: O'zbekiston Musulmonlar idorasi jadvali bilan 1-3 daqiqa farq
# bo'lishi mumkin. Keyinroq islom.uz bilan solishtirib sozlaymiz.
PARAMS = {"method": 3, "school": 1}

_cache: dict[tuple[str, date], dict[str, datetime]] = {}


async def get_prayer_times(city: str = DEFAULT_CITY, day: date | None = None) -> dict[str, datetime]:
    """Berilgan shahar va kun uchun 5 mahal namoz vaqtini qaytaradi.

    Natija: {"Bomdod": datetime, "Peshin": datetime, ...} (tz-aware)
    """
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
    result: dict[str, datetime] = {}
    for api_key, uz_name in API_TO_UZ.items():
        hh, mm = timings[api_key].split(" ")[0].split(":")
        result[uz_name] = datetime(day.year, day.month, day.day, int(hh), int(mm), tzinfo=tz)

    # Eski kunlarni keshdan tozalash
    for k in [k for k in _cache if k[1] < day]:
        del _cache[k]
    _cache[key] = result
    return result
