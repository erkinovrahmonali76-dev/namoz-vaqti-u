import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "YO'LDOSH UZ"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# Yo'nalishlar uchun shaharlar
CITIES = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Namangan", "Farg'ona",
    "Qarshi", "Nukus", "Urganch", "Termiz", "Jizzax", "Guliston", "Navoiy",
]
