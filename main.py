import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db
from cities import CITIES
from config import BOT_NAME, BOT_TOKEN
from prayer_times import get_prayer_times

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


def cities_keyboard():
    kb = InlineKeyboardBuilder()
    for name in CITIES:
        kb.add(InlineKeyboardButton(text=name, callback_data=f"city:{name}"))
    kb.adjust(2)
    return kb.as_markup()


async def times_text(city: str) -> str:
    times = await get_prayer_times(city)
    lines = [f"🕌 <b>{city}</b> — bugungi namoz vaqtlari:\n"]
    for name, t in times.items():
        lines.append(f"▫️ {name}: <b>{t.strftime('%H:%M')}</b>")
    return "\n".join(lines)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await db.add_user(message.chat.id)
    await message.answer(
        f"Assalomu alaykum! 🌙 <b>{BOT_NAME}</b> botiga xush kelibsiz.\n\n"
        "Men namoz vaqti yaqinlashganda sizga eslatib turaman.\n"
        "Avval shahringizni tanlang:",
        reply_markup=cities_keyboard(),
    )


@dp.message(Command("shahar"))
async def cmd_city(message: Message):
    await message.answer("Shahringizni tanlang:", reply_markup=cities_keyboard())


@dp.callback_query(F.data.startswith("city:"))
async def on_city(call: CallbackQuery):
    city = call.data.split(":", 1)[1]
    if city not in CITIES:
        await call.answer("Noma'lum shahar", show_alert=True)
        return
    await db.set_city(call.message.chat.id, city)
    await call.answer(f"{city} tanlandi ✅")
    try:
        text = await times_text(city)
    except Exception:
        logging.exception("Namoz vaqtlarini olishda xato")
        text = f"✅ Shahar: {city}. Vaqtlarni hozir olib bo'lmadi, birozdan so'ng /vaqt yuboring."
    await call.message.answer(
        text + "\n\n🔔 Namozga <b>15 daqiqa</b> qolganda va namoz vaqti kirganda xabar beraman."
    )


@dp.message(Command("vaqt"))
async def cmd_times(message: Message):
    city = await db.get_city(message.chat.id)
    try:
        await message.answer(await times_text(city))
    except Exception:
        logging.exception("Namoz vaqtlarini olishda xato")
        await message.answer("Vaqtlarni hozir olib bo'lmadi. Birozdan so'ng urinib ko'ring.")


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    await db.deactivate_user(message.chat.id)
    await message.answer("Eslatmalar o'chirildi. Qayta yoqish uchun /start yuboring.")


async def main():
    await db.init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
