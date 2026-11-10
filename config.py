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

# Viloyatlar va ularning asosiy shahar/tumanlari.
# Haydovchi bu ro'yxatda yo'q joyni ham o'zi yozib qo'sha oladi.
REGIONS = {
    "Toshkent shahri": ["Toshkent"],
    "Toshkent viloyati": ["Nurafshon", "Chirchiq", "Angren", "Olmaliq", "Bekobod", "Yangiyo'l", "Ohangaron"],
    "Andijon viloyati": ["Andijon", "Asaka", "Xonobod", "Shahrixon", "Marhamat", "Paxtaobod", "Qo'rg'ontepa"],
    "Farg'ona viloyati": ["Farg'ona", "Qo'qon", "Marg'ilon", "Quvasoy", "Yaypan", "Beshariq", "Rishton", "Oltiariq", "Bag'dod"],
    "Namangan viloyati": ["Namangan", "Chust", "Pop", "Chortoq", "Uchqo'rg'on", "Kosonsoy"],
    "Samarqand viloyati": ["Samarqand", "Kattaqo'rg'on", "Urgut", "Pastdarg'om", "Ishtixon"],
    "Buxoro viloyati": ["Buxoro", "G'ijduvon", "Kogon", "Vobkent", "Qorako'l"],
    "Navoiy viloyati": ["Navoiy", "Zarafshon", "Uchquduq", "Xatirchi", "Nurota"],
    "Qashqadaryo viloyati": ["Qarshi", "Shahrisabz", "Kitob", "Muborak", "G'uzor", "Yakkabog'"],
    "Surxondaryo viloyati": ["Termiz", "Denov", "Sherobod", "Boysun", "Sariosiyo"],
    "Jizzax viloyati": ["Jizzax", "Zomin", "Forish", "G'allaorol", "Do'stlik"],
    "Sirdaryo viloyati": ["Guliston", "Yangiyer", "Shirin", "Boyovut"],
    "Xorazm viloyati": ["Urganch", "Xiva", "Shovot", "Xonqa"],
    "Qoraqalpog'iston": ["Nukus", "Qo'ng'irot", "Xo'jayli", "To'rtko'l", "Beruniy"],
}

# Takliflar uchun tekis ro'yxat
PLACES = [place for places in REGIONS.values() for place in places]
