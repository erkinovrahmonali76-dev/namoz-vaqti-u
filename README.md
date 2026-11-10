[README (2).md](https://github.com/user-attachments/files/34629224/README.2.md)
# YO'LDOSH UZ

Telegram Mini App: shaharlararo yo'lovchi va haydovchilarni bog'laydi.

## Imkoniyatlar
1. Haydovchi e'lon beradi: qayerdan, qayerga, sana, vaqt, bo'sh joylar, narx, telefon
2. E'lon avtomatik `@yoldoshuzz` kanaliga joylanadi (bekor qilinsa, post ham yangilanadi)
3. Yo'lovchi qidiradi va joy band qiladi, haydovchiga botdan xabar boradi
4. Ilovadan foydalanish uchun kanalga majburiy obuna
5. Bekor qilishda sabab so'raladi (haydovchi va yo'lovchi uchun alohida variantlar)
6. "Mening e'lonlarim" va "Mening bronlarim" bo'limlari

## Tuzilishi
```
yoldosh/
├── main.py          # FastAPI server + bot webhook
├── config.py        # sozlamalar
├── db.py            # baza (PostgreSQL)
├── auth.py          # initData tekshirish + kanalga obuna
├── bot.py           # Telegram bot (aiogram)
├── api.py           # Mini App uchun API
└── webapp/index.html
```

## Muhim
- Botni kanalga **admin** qiling (xabar yuborish huquqi bilan).
- `.env.example` ni `.env` ga nusxalab to'ldiring (Render'da Environment bo'limiga kiriting).
- Baza jadvallari ishga tushganda avtomatik yangilanadi.

## Sabablar statistikasi
```sql
SELECT cancel_reason, count(*) FROM bookings WHERE status='cancelled' GROUP BY 1 ORDER BY 2 DESC;
```
