import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "YO'LDOSH UZ"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
# Render o'zi RENDER_EXTERNAL_URL beradi, shuning uchun WEBAPP_URL majburiy emas
WEBAPP_URL = (os.getenv("WEBAPP_URL") or os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Majburiy obuna va e'lonlar kanali
CHANNEL = os.getenv("CHANNEL", "@yoldoshuzz")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/yoldoshuzz")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")

# Faqat shu joylar tanlanadi: 12 viloyat + Qo'qon va Yaypan.
# Ro'yxatni o'zgartirmoqchi bo'lsangiz, faqat shu yerni tahrirlang.
PLACES = [
    "Andijon", "Buxoro", "Farg'ona", "Jizzax", "Namangan", "Navoiy",
    "Qashqadaryo", "Qo'qon", "Samarqand", "Sirdaryo", "Surxondaryo",
    "Toshkent", "Xorazm", "Yaypan",
]
