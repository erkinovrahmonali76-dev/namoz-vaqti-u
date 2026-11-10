from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import APP_NAME, BOT_TOKEN, CHANNEL_URL, WEBAPP_URL

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    args = command.args or ""

    # Kanal postidagi "Band qilish" tugmasi: /start ride_123
    if args.startswith("ride_") and args[5:].isdigit():
        ride_id = args[5:]
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚗 E'lonni ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}/app/?ride={ride_id}"))
        ]])
        await message.answer("Tanlangan e'lonni ochish uchun tugmani bosing:", reply_markup=kb)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Ilovani ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}/app/"))],
            [InlineKeyboardButton(text="📢 Kanalimiz", url=CHANNEL_URL)],
        ]
    )
    await message.answer(
        f"Assalomu alaykum! 👋 <b>{APP_NAME}</b> ga xush kelibsiz.\n\n"
        "Shaharlararo yo'lovchi va haydovchilarni topishtiruvchi ilova.\n"
        "Foydalanish uchun kanalimizga obuna bo'lgan bo'lishingiz kerak.\n\n"
        "Boshlash uchun tugmani bosing:",
        reply_markup=kb,
    )
