# Kurs sotuv boti (Telegram)

Kontent marketing video-kursini sotuvchi Telegram bot — aiogram 3.x asosida.

## Imkoniyatlar

- **Sotuv oqimi:** `/start` → salomlashuv → ro'yxatdan o'tish → to'lov ma'lumoti →
  chek (rasm) → ism/raqam → admin tasdig'i → kursga qo'shilish.
- **Chek izohidagi promo kod** avtomat chegirma qo'llaydi (muddat bilan).
- **Qayta jalb (retarget):** faol bo'lmagan foydalanuvchiga belgilangan
  daqiqalarda avtomat eslatmalar (matn, ovozli xabar, yumaloq video).
- **Admin panel (`/admin`):** barcha xabar/tugma matnlarini tahrirlash,
  retarget va rejalashtirilgan xabarlar, promo kodlar, narx, statistika,
  hammaga xabar yuborish.

## Ishga tushirish

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env      # .env ichiga o'z token va ADMIN_ID ni yozing
python bot.py
```

## Sozlash

`.env` fayli (GitHub'ga tushmaydi):

```
BOT_TOKEN=BotFather'dan olingan token
ADMIN_ID=Telegram ID raqamingiz
```

> ⚠️ `.env`, `bot.db` va zaxira fayllar `.gitignore` orqali repozitoriyaga
> hech qachon tushmaydi. Tokenni hech kimga bermang va GitHub'ga qo'ymang.
