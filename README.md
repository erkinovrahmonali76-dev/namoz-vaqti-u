[README (1).md](https://github.com/user-attachments/files/34626557/README.1.md)
# YO'LDOSH UZ

Telegram Mini App: shaharlararo yo'lovchi va haydovchilarni bog'laydi.

## Asosiy imkoniyatlar (MVP)
1. Haydovchi e'lon beradi: qayerdan, qayerga, sana, vaqt, bo'sh joylar, narx, telefon
2. Yo'lovchi qidiradi: yo'nalish va sana bo'yicha filtr
3. Yo'lovchi joy band qiladi, haydovchiga botdan xabar boradi
4. "Mening e'lonlarim" va "Mening bronlarim" bo'limlari

## Tuzilishi
```
yoldosh/
├── main.py          # FastAPI server + bot webhook
├── config.py        # sozlamalar
├── db.py            # baza (PostgreSQL)
├── bot.py           # Telegram bot (aiogram)
├── api.py           # Mini App uchun API
└── webapp/          # Mini App sahifasi (HTML/CSS/JS)
```

## Texnologiyalar
- Python, FastAPI, aiogram 3
- PostgreSQL (Neon yoki Supabase, bepul)
- GitHub -> Render (bitta Web Service)

## Qadamlar
1. Loyiha skeleti, BotFather, GitHub  <- hozir shu yerda
2. Baza (Neon) va jadvallar
3. Bot va webhook
4. API (e'lon qo'shish, qidirish, band qilish)
5. Mini App sahifasi
6. Render'ga joylash va BotFather'da Mini App ulash
