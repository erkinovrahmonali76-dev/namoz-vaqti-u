from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import APP_NAME, BOT_TOKEN, WEBAPP_URL

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Ilovani ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}/app/"))]
        ]
    )
    await message.answer(
        f"Assalomu alaykum! 👋 <b>{APP_NAME}</b> ga xush kelibsiz.\n\n"
        "Shaharlararo yo'lovchi va haydovchilarni topishtiruvchi ilova.\n"
        "Boshlash uchun tugmani bosing:",
        reply_markup=kb,
    )
