# Botni serverga (VPS) joylashtirish — 24/7 ishlashi uchun

Bu qo'llanma botni doim yoniq **Linux server (VPS)** da ishga tushiradi.
Server o'chib-yonса ham bot **avtomat qayta ishga tushadi** (`systemd`).

> Nega VPS? Telegram boti internetsiz ishlamaydi. Shaxsiy kompyuter o'chsa —
> bot to'xtaydi. VPS doim yoniq bo'lgani uchun bot 24/7 ishlaydi.

---

## 1. VPS olish

Arzon Ubuntu 22.04 / 24.04 serveri yetarli (1 GB RAM ham bo'ladi). Masalan:
Hetzner, DigitalOcean, Contabo, yoki mahalliy (Uzbekistan) provayderlar.

Serverni yaratganda **Ubuntu 22.04** ni tanlang va SSH orqali kiring:

```bash
ssh root@SERVER_IP
```

## 2. Kerakli dasturlar

```bash
apt update && apt install -y python3 python3-venv python3-pip git
```

## 3. Kodni yuklab olish

```bash
cd /opt
git clone https://github.com/Ikramovdev/OnAiRR.git kurs-bot
cd kurs-bot
```

## 4. Virtual muhit va kutubxonalar

```bash
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

## 5. Sozlamalar (.env)

`.env` faylini yarating (bu fayl GitHub'da yo'q — qo'lda yoziladi):

```bash
nano .env
```

Ichiga yozing (o'z qiymatlaringiz bilan):

```
BOT_TOKEN=BotFather'dan olingan token
ADMIN_ID=Telegram ID raqamingiz
```

Saqlash: `Ctrl+O`, `Enter`, keyin `Ctrl+X`.

## 6. systemd xizmatini o'rnatish (avtomat ishga tushirish)

```bash
cp deploy/kurs-bot.service /etc/systemd/system/kurs-bot.service
systemctl daemon-reload
systemctl enable kurs-bot      # server yonganda avtomat ishga tushadi
systemctl start kurs-bot       # hozir ishga tushiradi
```

> Agar kodni `/opt/kurs-bot` dan boshqa joyga qo'ygan bo'lsangiz,
> `kurs-bot.service` ichidagi `WorkingDirectory` va `ExecStart` yo'llarini moslang.

## 7. Holatni tekshirish

```bash
systemctl status kurs-bot         # ishlayaptimi?
journalctl -u kurs-bot -f         # jonli loglar (chiqish: Ctrl+C)
```

`Run polling for bot @...` chiqsa — bot ishlayapti. ✅

---

## Keyingi yangilanishlar (kod o'zgarganda)

```bash
cd /opt/kurs-bot
git pull
systemctl restart kurs-bot
```

## Foydali buyruqlar

```bash
systemctl stop kurs-bot       # to'xtatish
systemctl start kurs-bot      # yoqish
systemctl restart kurs-bot    # qayta yoqish
journalctl -u kurs-bot -n 50  # oxirgi 50 qator log
```

> ⚠️ `bot.db` (foydalanuvchilar bazasi) va `.env` serverda hosil bo'ladi va
> GitHub'ga tushmaydi. Vaqti-vaqti bilan `bot.db` ni zaxiralab turing.
