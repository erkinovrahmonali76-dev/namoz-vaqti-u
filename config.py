import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "NAMOZ VAQTI UZ"
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REMIND_BEFORE_MIN = int(os.getenv("REMIND_BEFORE_MIN", "15"))
NOTIFY_AT_TIME = os.getenv("NOTIFY_AT_TIME", "true").lower() == "true"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# Barcha 5 mahal namoz (Bomdod, Peshin, Asr, Shom, Xufton)
PRAYERS = ["Bomdod", "Peshin", "Asr", "Shom", "Xufton"]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring.")
