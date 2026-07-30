"""
==========================================================================
  KURS SOTUV BOTI (Telegram) — aiogram 3.x
==========================================================================
FOYDALANUVCHI OQIMI:
  /start
    └─ [welcome]  salomlashuv            → tugma "Ro'yxatdan o'tish"
         └─ [payment]  to'lov ma'lumoti  → tugma "To'lov qildim"
              └─ [ask_receipt]  "chekni yuboring"  → foydalanuvchi RASM yuboradi
                   (rasm izohida promo kod bo'lsa — chegirma qo'llanadi)
                   └─ [ask_contact]  "ism va raqam"  → foydalanuvchi MATN yuboradi
                        └─ [pending]  "qabul qildim, 24 soat"
                             └─ ADMINGA chek + ma'lumot + promo → ✅/❌
                                  ├─ ✅ → [approved]
                                  └─ ❌ → [rejected]

QAYTA JALB (retarget) — /start dan keyin faol bo'lmasa, avtomat yuboriladi:
  7-daqiqa   → 1-eslatma (+ "Imkoniyatdan foydalanish" → to'lovga qaytadi)
  17-daqiqa  → 2-eslatma
  29-daqiqa  → 3-eslatma (ovozli xabar bo'lishi mumkin)
  39-daqiqa  → 4-eslatma (yumaloq video bo'lishi mumkin)
  Foydalanuvchi to'lov ma'lumotlarini (ism+raqam) yuborsa — eslatmalar TO'XTAYDI.

ADMIN (/admin):
  • Barcha xabar/tugma matnlarini tahrirlash.
  • Qayta jalb (retarget) xabarlarini tahrirlash (vaqt, matn, media, tugma).
  • Ro'yxatdan o'tgandan / sotib olgandan keyin xabar rejalashtirish.
  • Promo kod qo'shish (muddat bilan) va o'chirish.
  • Hammaga xabar, statistika.

QOIDA: barcha vaqtlar butun MINUTda. Kod xatoga chidamli — bir foydalanuvchidagi
xato boshqalarga ta'sir qilmaydi, yuborilmagan xabar keyingi aylanishda qayta uriniladi.
==========================================================================
"""

import asyncio
import html as html_lib
import logging
import os
import sqlite3
import time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

# --------------------------------------------------------------------------
# 1-QISM: SOZLAMALAR
# --------------------------------------------------------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = "bot.db"
SCHEMA_VERSION = 3           # bazani yangilash uchun ichki versiya

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Admin tomonidagi (chekni tekshirish) tugmalari — foydalanuvchiga ko'rinmaydi.
APPROVE_BTN = "✅ Qabul qildim"
REJECT_BTN = "❌ Qabul qilmadim"

# Oqim bosqichlari (raqam kattalashgani sari — oldinga siljish).
STAGE_RANK = {
    "new": 0,          # /start bosildi
    "registered": 1,   # "Ro'yxatdan o'tish" bosildi (to'lov ma'lumoti ko'rsatildi)
    "paid_click": 2,   # "To'lov qildim" bosildi (chek kutilyapti)
    "receipt": 3,      # chek yuborildi (ism+raqam kutilyapti)
    "submitted": 4,    # ism+raqam yuborildi (admin ko'rib chiqishi kerak)
    "enrolled": 5,     # admin tasdiqladi
}

# Oqim xabarlari: (kalit, admin uchun nomi, matn, tugma matni)
DEFAULT_MESSAGES = [
    ("welcome", "1️⃣ Salomlashuv (/start)",
     "Assalomu alaykum! Katta o‘zgarishga tayyorligingizdan xursandmiz.\n\n"
     "🏆 Bizning maqsadimiz — O‘zbekistonda kuchli kontentmeykerlarni "
     "ko‘paytirib media bozorini yangi darajaga olib chiqish.\n\n"
     "Bu video-kurs kontent marketingdan sizni yangi darajaga olib chiqishiga "
     "ishonamiz.",
     "✅ Ro'yxatdan o'tish"),

    ("payment", "2️⃣ To'lov ma'lumoti",
     "💳 <b>To'lov ma'lumotlari</b>\n\n"
     "Karta: <b>8600 1234 5678 9012</b>\n"
     "Egasi: <b>Ism Familiya</b>\n\n"
     "To'lovni amalga oshirib, pastdagi tugmani bosing 👇",
     "💰 To'lov qildim"),

    ("ask_receipt", "3️⃣ Chek so'rash",
     "Ajoyib, to‘lov qilgan chekingizni skrinshot qilib yuboring 👇",
     ""),

    ("ask_contact", "4️⃣ Ism va raqam so'rash",
     "To‘lovni qabul qilishim uchun Ismingiz va raqamingizni yuboring 👇",
     ""),

    ("pending", "5️⃣ Qabul qilindi (kutish)",
     "🥳 Ajoyib! To‘lovingizni qabul qildim.\n\n"
     "⌛ 24 soat ichida, chekingizni tekshirib to‘lov qilgan kurslaringiz "
     "uchun havola beramiz.",
     ""),

    ("approved", "6️⃣ To'lov tasdiqlandi",
     "Darsliklarga qo‘shilganingiz bilan tabriklayman. 🎉\n\n"
     "Havola: <i>(admin bu yerga kurs/kanal linkini qo'yadi)</i>",
     ""),

    ("rejected", "7️⃣ To'lov rad etildi",
     "To‘lovingiz qabul qilinmadi ❌\n\n"
     "Yuborgan chekingizda bizga to‘lov qilganingiz ko‘rsatilmagan, darslarga "
     "qo‘shilishni istasangiz to‘lovni to‘g‘ri amalga oshirib qayta yuboring.",
     ""),
]

CORE_KEYS = [k for k, _, _, _ in DEFAULT_MESSAGES]

# Qaysi oqim xabarida tugma bosilsa, qaysi callback ishlaydi.
CORE_BUTTON_CB = {
    "welcome": "reg",     # → to'lov ma'lumotini ko'rsatadi
    "payment": "paid",    # → chek so'raydi
}

# Qayta jalb (retarget) va rejalashtirilgan xabarlarning standart holati.
# (kind, anchor, after_minutes, text, media_type, file_id, button_text)
DEFAULT_TIMED = [
    ("retarget", "start", 7,
     "📹 Aytishni unitibman, 200.000 so‘mlik “Montaj” mini kursi 10 daqiqa "
     "ichida harid qilganlar uchun bepulga beriladi.\n"
     "⌛ Sizda esa atiga 9 daqiqa qoldi... AI dan foydalanish darsini ham "
     "qo‘shib beraman va bu imkoniyatdan foydalanish uchun 9 daqiqa vaqtingiz qoldi",
     "", "", "🔥 Imkoniyatdan foydalanish"),

    ("retarget", "start", 17,
     "So‘nggi 2 daqiqa.\n"
     "Jami: 1.000.000 so‘mlik 2ta kursni 2 daqiqa ichida 480.000 so‘mga "
     "qo‘lga kiritasiz.\n"
     "Bunday imkoniyat boshqa bo‘lmaydi, hozir yoki hech qachon.",
     "", "", "🔥 Imkoniyatdan foydalanish"),

    ("retarget", "start", 29,
     "Afsus {ism}\n"
     "Montaj kursi asl narxiga qaytdi, bonusni ololmaganingizdan afsusdaman 😞",
     "", "", "🔥 Imkoniyatdan foydalanish"),

    ("retarget", "start", 39,
     "So‘nggi imkoniyat — bu taklif yopilmoqda. Qo‘shilish uchun tugmani bosing 👇",
     "", "", "🔥 Imkoniyatdan foydalanish"),
]

DEFAULT_SETTINGS = {
    "price": "0",   # 0 = narx ko'rsatilmaydi (matnlarda yozilgan bo'lsa yetarli)
}


# --------------------------------------------------------------------------
# 2-QISM: MA'LUMOTLAR BAZASI
# --------------------------------------------------------------------------

def db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    return con


def _has_column(cur, table, column) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return column in [r[1] for r in cur.fetchall()]


def _add_column(cur, table, column, coldef):
    if not _has_column(cur, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coldef}")


def _schema_version(cur) -> int:
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("SELECT value FROM settings WHERE key = 'schema_version'")
    row = cur.fetchone()
    try:
        return int(row[0]) if row else 0
    except (TypeError, ValueError):
        return 0


def init_db():
    con = db()
    cur = con.cursor()
    ver = _schema_version(cur)

    # --- Bir martalik ko'chirish: eski (v<3) tuzilma yangisiga ------------
    # users/messages semantikasi butunlay o'zgargani uchun ularni qayta quramiz.
    # Admin tahrir qilgan matnlar keyingi ishga tushirishlarda saqlanadi
    # (chunki drop faqat versiya oshganda bir marta bajariladi).
    if ver < 3:
        logging.info("Baza yangilanmoqda: v%s -> v3", ver)
        for t in ("users", "messages", "checkins", "checkin_sent"):
            cur.execute(f"DROP TABLE IF EXISTS {t}")

    # --- Foydalanuvchilar ---
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            full_name       TEXT DEFAULT '',
            username        TEXT DEFAULT '',
            started_at      INTEGER,
            registered_at   INTEGER,
            stage           TEXT DEFAULT 'new',
            receipt_type    TEXT DEFAULT '',
            receipt_file_id TEXT DEFAULT '',
            contact         TEXT DEFAULT '',
            promo_code      TEXT DEFAULT '',
            discount        INTEGER DEFAULT 0,
            submitted_at    INTEGER,
            paid_at         INTEGER,
            enrolled        INTEGER DEFAULT 0
        )"""
    )
    for col, definition in [
        ("registered_at", "INTEGER"),
        ("stage", "TEXT DEFAULT 'new'"),
        ("receipt_type", "TEXT DEFAULT ''"),
        ("receipt_file_id", "TEXT DEFAULT ''"),
        ("contact", "TEXT DEFAULT ''"),
        ("promo_code", "TEXT DEFAULT ''"),
        ("discount", "INTEGER DEFAULT 0"),
        ("submitted_at", "INTEGER"),
        ("paid_at", "INTEGER"),
        ("enrolled", "INTEGER DEFAULT 0"),
    ]:
        _add_column(cur, "users", col, definition)

    # --- Oqim xabarlari ---
    cur.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            key         TEXT PRIMARY KEY,
            title       TEXT,
            text        TEXT,
            media_type  TEXT DEFAULT '',
            file_id     TEXT DEFAULT '',
            button_text TEXT DEFAULT '',
            enabled     INTEGER DEFAULT 1
        )"""
    )
    for key, title, text, button in DEFAULT_MESSAGES:
        cur.execute(
            """INSERT OR IGNORE INTO messages (key, title, text, button_text)
               VALUES (?, ?, ?, ?)""",
            (key, title, text, button),
        )
        cur.execute("UPDATE messages SET title = ? WHERE key = ?", (title, key))

    # --- Sozlamalar ---
    for k, v in DEFAULT_SETTINGS.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # --- Promo kodlar (muddat bilan) ---
    cur.execute(
        """CREATE TABLE IF NOT EXISTS promo_codes (
            code       TEXT PRIMARY KEY,
            discount   INTEGER,
            expires_at INTEGER
        )"""
    )
    _add_column(cur, "promo_codes", "expires_at", "INTEGER")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS promo_uses (
            code    TEXT,
            user_id INTEGER,
            used_at INTEGER,
            PRIMARY KEY (code, user_id)
        )"""
    )

    # --- Vaqt bilan yuboriladigan xabarlar (retarget + rejalashtirilgan) ---
    cur.execute(
        """CREATE TABLE IF NOT EXISTS timed (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            kind          TEXT,      -- 'retarget' | 'sched'
            anchor        TEXT,      -- 'start' | 'register' | 'paid'
            after_minutes INTEGER,
            text          TEXT DEFAULT '',
            media_type    TEXT DEFAULT '',
            file_id       TEXT DEFAULT '',
            button_text   TEXT DEFAULT '',
            enabled       INTEGER DEFAULT 1
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS timed_sent (
            timed_id INTEGER,
            user_id  INTEGER,
            sent_at  INTEGER,
            PRIMARY KEY (timed_id, user_id)
        )"""
    )
    # Standart retarget xabarlarini faqat bir marta (jadval bo'sh bo'lsa) seed qilamiz.
    cur.execute("SELECT COUNT(*) FROM timed")
    if cur.fetchone()[0] == 0:
        for kind, anchor, mins, text, mtype, fid, btn in DEFAULT_TIMED:
            cur.execute(
                """INSERT INTO timed
                   (kind, anchor, after_minutes, text, media_type, file_id, button_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (kind, anchor, mins, text, mtype, fid, btn),
            )

    cur.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    con.commit()
    con.close()


# --- Sozlamalar ---
def get_setting(key: str) -> str:
    con = db(); cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone(); con.close()
    return row[0] if row else DEFAULT_SETTINGS.get(key, "")


def set_setting(key: str, value: str):
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    con.commit(); con.close()


def get_int(key: str) -> int:
    try:
        return int(get_setting(key))
    except (TypeError, ValueError):
        return 0


def fmt(n: int) -> str:
    """199000 -> '199 000'"""
    return f"{n:,}".replace(",", " ")


def preview(text: str, limit: int = 500) -> str:
    """Admin paneli uchun xavfsiz (ekranlab kesilgan) ko'rinish."""
    text = text or ""
    kesilgan = text[:limit]
    qoldiq = "…" if len(text) > limit else ""
    return html_lib.escape(kesilgan) + qoldiq


def personalize(text: str, user_row) -> str:
    """{ism} / {name} o'rniga foydalanuvchi ismini qo'yadi (xavfsiz)."""
    if not text:
        return text or ""
    name = ""
    if user_row is not None:
        try:
            name = (user_row["full_name"] or "")
        except (KeyError, IndexError, TypeError):
            name = ""
    name = html_lib.escape(name)
    return text.replace("{ism}", name).replace("{name}", name)


# --- Oqim xabarlari ---
def get_message(key: str):
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM messages WHERE key = ?", (key,))
    row = cur.fetchone(); con.close()
    return row


def all_messages():
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM messages")
    rows = cur.fetchall(); con.close()
    return sorted(rows, key=lambda r: CORE_KEYS.index(r["key"]) if r["key"] in CORE_KEYS else 99)


def update_message(key: str, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    con = db(); cur = con.cursor()
    cur.execute(f"UPDATE messages SET {sets} WHERE key = ?", (*fields.values(), key))
    con.commit(); con.close()


# --- Foydalanuvchilar ---
def add_user(user):
    con = db(); cur = con.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO users (user_id, full_name, username, started_at, stage)
           VALUES (?, ?, ?, ?, 'new')""",
        (user.id, user.full_name or "", user.username or "", int(time.time())),
    )
    # Ism/username o'zgargan bo'lsa yangilab qo'yamiz
    cur.execute(
        "UPDATE users SET full_name = ?, username = ? WHERE user_id = ?",
        (user.full_name or "", user.username or "", user.id),
    )
    con.commit(); con.close()


def get_user(user_id: int):
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone(); con.close()
    return row


def mark(user_id: int, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    con = db(); cur = con.cursor()
    cur.execute(f"UPDATE users SET {sets} WHERE user_id = ?", (*fields.values(), user_id))
    con.commit(); con.close()


def stage_of(user_row) -> str:
    try:
        return user_row["stage"] or "new"
    except (KeyError, IndexError, TypeError):
        return "new"


def advance_stage(user_id: int, user_row, new_stage: str):
    """Bosqichni faqat OLDINGA suradi (orqaga tushirmaydi)."""
    cur = STAGE_RANK.get(stage_of(user_row), 0)
    if STAGE_RANK.get(new_stage, 0) > cur:
        mark(user_id, stage=new_stage)


def is_enrolled(user_row) -> bool:
    try:
        return bool(user_row and user_row["enrolled"])
    except (KeyError, IndexError, TypeError):
        return False


def funnel_done(user_row) -> bool:
    """To'lov ma'lumotini yuborgan yoki sotib olgan — retarget to'xtaydi."""
    return is_enrolled(user_row) or STAGE_RANK.get(stage_of(user_row), 0) >= STAGE_RANK["submitted"]


def all_user_ids() -> list[int]:
    con = db(); cur = con.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r[0] for r in cur.fetchall()]; con.close()
    return ids


def stats() -> dict:
    con = db(); cur = con.cursor()
    cur.execute(
        """SELECT COUNT(*) AS jami,
                  COALESCE(SUM(registered_at IS NOT NULL), 0) AS reg,
                  COALESCE(SUM(submitted_at IS NOT NULL), 0) AS sub,
                  COALESCE(SUM(enrolled), 0) AS sotib
           FROM users"""
    )
    r = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM promo_uses")
    promo = cur.fetchone()[0]
    con.close()
    return {"jami": r["jami"], "reg": r["reg"], "sub": r["sub"],
            "sotib": r["sotib"], "promo": promo}


def reset_funnel(user_id: int):
    """/start qayta bosilganda oqimni boshidan boshlaydi (retargetlarni ham qayta yoqadi)."""
    mark(user_id, stage="new", started_at=int(time.time()),
         registered_at=None, submitted_at=None,
         receipt_type="", receipt_file_id="", contact="",
         promo_code="", discount=0)
    con = db(); cur = con.cursor()
    cur.execute(
        """DELETE FROM timed_sent WHERE user_id = ? AND timed_id IN
           (SELECT id FROM timed WHERE kind = 'retarget')""",
        (user_id,),
    )
    con.commit(); con.close()


# --- Promo kodlar ---
def add_promo(code: str, discount: int, days: int = 0):
    expires = int(time.time()) + days * 86400 if days > 0 else None
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO promo_codes (code, discount, expires_at) VALUES (?, ?, ?)",
        (code.upper(), discount, expires),
    )
    con.commit(); con.close()


def get_promo(code: str):
    """Amaldagi (muddati o'tmagan) promoning chegirmasini qaytaradi, aks holda None."""
    con = db(); cur = con.cursor()
    cur.execute("SELECT discount, expires_at FROM promo_codes WHERE code = ?", (code.upper(),))
    row = cur.fetchone(); con.close()
    if not row:
        return None
    disc, exp = row["discount"], row["expires_at"]
    if exp is not None and exp < int(time.time()):
        return None
    return disc


def delete_promo(code: str):
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM promo_codes WHERE code = ?", (code.upper(),))
    con.commit(); con.close()


def list_promos():
    """[(kod, foiz, expires_at, nechta_ishlatgan), ...]"""
    con = db(); cur = con.cursor()
    cur.execute(
        """SELECT p.code, p.discount, p.expires_at,
                  (SELECT COUNT(*) FROM promo_uses u WHERE u.code = p.code) AS soni
           FROM promo_codes p ORDER BY p.code"""
    )
    rows = [(r["code"], r["discount"], r["expires_at"], r["soni"]) for r in cur.fetchall()]
    con.close()
    return rows


def promo_already_used(user_id: int) -> str | None:
    con = db(); cur = con.cursor()
    cur.execute(
        "SELECT code FROM promo_uses WHERE user_id = ? ORDER BY used_at LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone(); con.close()
    return row[0] if row else None


def record_promo_use(code: str, user_id: int):
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO promo_uses (code, user_id, used_at) VALUES (?, ?, ?)",
        (code.upper(), user_id, int(time.time())),
    )
    con.commit(); con.close()


def find_promo_in_text(text: str) -> str | None:
    """Matn (chek izohi) ichidan amaldagi promo kodni topadi."""
    if not text:
        return None
    for word in text.replace("\n", " ").split():
        w = word.strip().strip(".,!?:;#").upper()
        if w and get_promo(w) is not None:
            return w
    return None


def final_price(user_row) -> int:
    base = get_int("price")
    disc = 0
    try:
        disc = (user_row["discount"] if user_row else 0) or 0
    except (KeyError, IndexError, TypeError):
        disc = 0
    return base * (100 - disc) // 100 if disc else base


# --- Vaqtli xabarlar (timed) ---
def list_timed(kind: str | None = None):
    con = db(); cur = con.cursor()
    if kind:
        cur.execute("SELECT * FROM timed WHERE kind = ? ORDER BY after_minutes, id", (kind,))
    else:
        cur.execute("SELECT * FROM timed ORDER BY kind, after_minutes, id")
    rows = cur.fetchall(); con.close()
    return rows


def get_timed(tid: int):
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM timed WHERE id = ?", (tid,))
    row = cur.fetchone(); con.close()
    return row


def add_timed(kind, anchor, minutes, text="", media_type="", file_id="", button_text="") -> int:
    con = db(); cur = con.cursor()
    cur.execute(
        """INSERT INTO timed
           (kind, anchor, after_minutes, text, media_type, file_id, button_text)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (kind, anchor, minutes, text, media_type, file_id, button_text),
    )
    tid = cur.lastrowid
    con.commit(); con.close()
    return tid


def update_timed(tid: int, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    con = db(); cur = con.cursor()
    cur.execute(f"UPDATE timed SET {sets} WHERE id = ?", (*fields.values(), tid))
    con.commit(); con.close()


def delete_timed(tid: int):
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM timed WHERE id = ?", (tid,))
    cur.execute("DELETE FROM timed_sent WHERE timed_id = ?", (tid,))
    con.commit(); con.close()


def timed_receivers(tid: int) -> int:
    con = db(); cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM timed_sent WHERE timed_id = ?", (tid,))
    n = cur.fetchone()[0]; con.close()
    return n


def mark_timed_sent(tid: int, user_id: int):
    con = db(); cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO timed_sent (timed_id, user_id, sent_at) VALUES (?, ?, ?)",
        (tid, user_id, int(time.time())),
    )
    con.commit(); con.close()


# --------------------------------------------------------------------------
# 3-QISM: BOT VA YUBORISH YORDAMCHILARI
# --------------------------------------------------------------------------
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


MEDIA_LABEL = {
    "": "matn", "photo": "rasm", "video": "video", "animation": "GIF",
    "document": "fayl", "voice": "ovozli", "video_note": "yumaloq video",
}


def extract_media(message: Message) -> tuple[str, str, str]:
    """Adminning xabaridan (media_type, file_id, text) ni ajratib oladi."""
    media_type, file_id = "", ""
    if message.photo:
        media_type, file_id = "photo", message.photo[-1].file_id
    elif message.video:
        media_type, file_id = "video", message.video.file_id
    elif message.animation:
        media_type, file_id = "animation", message.animation.file_id
    elif message.voice:
        media_type, file_id = "voice", message.voice.file_id
    elif message.audio:
        media_type, file_id = "voice", message.audio.file_id
    elif message.video_note:
        media_type, file_id = "video_note", message.video_note.file_id
    elif message.document:
        media_type, file_id = "document", message.document.file_id
    text = (message.html_text or "") if (message.text or message.caption) else ""
    return media_type, file_id, text


async def deliver(chat_id: int, text: str, media_type: str, file_id: str,
                  kb: InlineKeyboardMarkup | None, user_row=None):
    """
    Bitta xabarni turi qanday bo'lishidan qat'i nazar yuboradi.
    Muvaffaqiyatda — Message, aks holda None qaytaradi.
    TelegramForbiddenError (bloklangan) yuqoriga uzatiladi — chaqiruvchi hal qiladi.
    """
    text = personalize(text or "", user_row)
    mt = (media_type or "").strip()
    fid = (file_id or "").strip()
    cap = text or None
    try:
        if mt == "photo" and fid:
            return await bot.send_photo(chat_id, fid, caption=cap, reply_markup=kb)
        if mt == "video" and fid:
            return await bot.send_video(chat_id, fid, caption=cap, reply_markup=kb)
        if mt == "animation" and fid:
            return await bot.send_animation(chat_id, fid, caption=cap, reply_markup=kb)
        if mt == "document" and fid:
            return await bot.send_document(chat_id, fid, caption=cap, reply_markup=kb)
        if mt == "voice" and fid:
            return await bot.send_voice(chat_id, fid, caption=cap, reply_markup=kb)
        if mt == "video_note" and fid:
            # Yumaloq video izoh (caption) qo'llab-quvvatlamaydi:
            # matn bo'lsa — alohida xabar, so'ng video + tugma.
            if text.strip():
                try:
                    await bot.send_message(chat_id, text)
                except TelegramForbiddenError:
                    raise
                except Exception:
                    pass
            return await bot.send_video_note(chat_id, fid, reply_markup=kb)
        # Media yo'q — oddiy matn
        if not text.strip():
            if kb is not None:
                return await bot.send_message(chat_id, "👇", reply_markup=kb)
            return None
        return await bot.send_message(chat_id, text, reply_markup=kb,
                                      disable_web_page_preview=False)
    except TelegramForbiddenError:
        raise
    except Exception as e:
        logging.exception("deliver(chat=%s, mt=%s): %s", chat_id, mt, e)
        return None


async def send_core(chat_id: int, key: str, user_row):
    """Oqim xabarini (mos tugmasi bilan) yuboradi. O'chirilgan bo'lsa — None."""
    m = get_message(key)
    if not m or not m["enabled"]:
        logging.warning("Oqim xabari yo'q yoki o'chirilgan: %s", key)
        return None
    kb = None
    btn = (m["button_text"] or "").strip()
    if btn and key in CORE_BUTTON_CB:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=btn, callback_data=CORE_BUTTON_CB[key])
        ]])
    return await deliver(chat_id, m["text"], m["media_type"], m["file_id"], kb, user_row)


def retarget_kb(row) -> InlineKeyboardMarkup | None:
    btn = (row["button_text"] or "").strip()
    if not btn:
        return None
    # Barcha retarget tugmalari to'lov ma'lumotiga qaytaradi (reg).
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=btn, callback_data="reg")
    ]])


# --------------------------------------------------------------------------
# 4-QISM: FOYDALANUVCHI OQIMI
# --------------------------------------------------------------------------

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        return await message.answer(
            "🔧 Siz adminsiz. Panel uchun /admin ni bosing."
        )
    await state.clear()
    add_user(message.from_user)
    row = get_user(message.from_user.id)
    logging.info("▶️ /start: user=%s stage=%s", message.from_user.id, stage_of(row))

    if is_enrolled(row):
        return await send_core(message.chat.id, "approved", row)
    if stage_of(row) == "submitted":
        # Chek yuborilgan, admin javobini kutyapti — takroran adminni bezovta qilmaymiz
        return await send_core(message.chat.id, "pending", row)

    # Aks holda oqimni boshidan boshlaymiz
    reset_funnel(message.from_user.id)
    row = get_user(message.from_user.id)
    await send_core(message.chat.id, "welcome", row)


@dp.callback_query(F.data == "reg")
async def on_register(call: CallbackQuery):
    """“Ro'yxatdan o'tish” / “Imkoniyatdan foydalanish” → to'lov ma'lumoti."""
    uid = call.from_user.id
    if is_admin(uid):
        return await call.answer()
    add_user(call.from_user)
    row = get_user(uid)
    if is_enrolled(row):
        await send_core(call.message.chat.id, "approved", row)
        return await call.answer()

    if not row["registered_at"]:
        mark(uid, registered_at=int(time.time()))
    advance_stage(uid, row, "registered")
    row = get_user(uid)
    await send_core(call.message.chat.id, "payment", row)
    await call.answer()


@dp.callback_query(F.data == "paid")
async def on_paid_click(call: CallbackQuery):
    """“To'lov qildim” → chek so'raymiz."""
    uid = call.from_user.id
    if is_admin(uid):
        return await call.answer()
    add_user(call.from_user)
    row = get_user(uid)
    if is_enrolled(row):
        await send_core(call.message.chat.id, "approved", row)
        return await call.answer()

    advance_stage(uid, row, "paid_click")
    row = get_user(uid)
    await send_core(call.message.chat.id, "ask_receipt", row)
    await call.answer()


@dp.message(StateFilter(None), F.photo | F.document | F.video | F.animation)
async def on_receipt(message: Message):
    """Foydalanuvchi chek (rasm/fayl) yubordi."""
    uid = message.from_user.id
    if is_admin(uid):
        return
    add_user(message.from_user)
    row = get_user(uid)

    if is_enrolled(row):
        return await send_core(message.chat.id, "approved", row)

    st = stage_of(row)
    # Chekni faqat oqimga kirgan (to'lov ma'lumotini ko'rgan) foydalanuvchidan qabul qilamiz.
    if STAGE_RANK.get(st, 0) < STAGE_RANK["registered"] or st == "submitted":
        return  # begona rasm — jim turamiz

    media_type, file_id, _ = extract_media(message)
    if not file_id:
        return

    # Chek izohidagi promo kod — chegirma (faqat bir marta)
    caption = message.caption or ""
    if not (row["promo_code"] or "").strip() and not promo_already_used(uid):
        code = find_promo_in_text(caption)
        if code:
            disc = get_promo(code)
            if disc is not None:
                mark(uid, promo_code=code, discount=disc)
                record_promo_use(code, uid)
                logging.info("🎟 Promo (chekdan): user=%s kod=%s -%s%%", uid, code, disc)

    mark(uid, receipt_type=media_type, receipt_file_id=file_id)
    advance_stage(uid, row, "receipt")
    row = get_user(uid)
    await send_core(message.chat.id, "ask_contact", row)


@dp.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def on_contact(message: Message):
    """Foydalanuvchi ism va raqamini yubordi."""
    uid = message.from_user.id
    if is_admin(uid):
        return
    add_user(message.from_user)
    row = get_user(uid)

    if is_enrolled(row):
        return
    # Ism+raqam faqat chek yuborilgandan keyin kutiladi. Aks holda — jim.
    if stage_of(row) != "receipt":
        return

    contact = (message.text or "").strip()
    if not contact:
        return

    mark(uid, contact=contact, submitted_at=int(time.time()))
    advance_stage(uid, row, "submitted")
    row = get_user(uid)

    # Foydalanuvchiga tasdiq
    await send_core(message.chat.id, "pending", row)
    # Adminga chek + ma'lumot
    await notify_admin(row)


async def notify_admin(row):
    """Adminga chek media + foydalanuvchi ma'lumoti + promo, ✅/❌ tugmalar bilan."""
    uid = row["user_id"]
    lines = [
        "🧾 <b>Yangi to'lov (tekshirish kerak)</b>", "",
        f"👤 {html_lib.escape(row['full_name'] or '')}",
        f"🆔 <code>{uid}</code>",
        f"🔗 @{row['username'] or 'yoq'}",
        f"✍️ Kiritgan: <b>{html_lib.escape(row['contact'] or '')}</b>",
    ]
    code = (row["promo_code"] or "").strip()
    disc = (row["discount"] or 0)
    if code:
        lines.append(f"🎟 Promo: <b>{code}</b> (-{disc}%)")
    price = final_price(row)
    if price > 0:
        lines.append(f"💰 To'lashi kerak: <b>{fmt(price)} so'm</b>")
    caption = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=APPROVE_BTN, callback_data=f"ok:{uid}"),
        InlineKeyboardButton(text=REJECT_BTN, callback_data=f"no:{uid}"),
    ]])

    rtype = (row["receipt_type"] or "").strip()
    rfid = (row["receipt_file_id"] or "").strip()
    sent = None
    try:
        if rtype and rfid:
            sent = await deliver(ADMIN_ID, caption, rtype, rfid, kb)
    except TelegramForbiddenError:
        sent = None
    except Exception as e:
        logging.exception("notify_admin media: %s", e)
        sent = None
    if sent is None:
        # Media yuborilmadi — hech bo'lmasa matnli xabar + tugma
        try:
            await bot.send_message(
                ADMIN_ID, caption + "\n\n⚠️ (chek mediasi yuborilmadi)", reply_markup=kb)
        except Exception as e:
            logging.exception("notify_admin text: %s", e)


@dp.callback_query(F.data.startswith("ok:"))
async def approve(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Faqat admin uchun.", show_alert=True)
    try:
        uid = int(call.data.split(":")[1])
    except (ValueError, IndexError):
        return await call.answer("Xato.", show_alert=True)

    row = get_user(uid)
    sent = await send_core(uid, "approved", row)
    if sent is None:
        return await call.answer(
            "Xabar yuborilmadi (o'chirilgan yoki foydalanuvchi botni bloklagan).",
            show_alert=True)
    mark(uid, enrolled=1, stage="enrolled", paid_at=int(time.time()))
    try:
        base = call.message.caption if call.message.caption is not None else call.message.text
        new = (base or "") + "\n\n✅ QABUL QILINDI"
        if call.message.caption is not None:
            await call.message.edit_caption(caption=new, reply_markup=None)
        else:
            await call.message.edit_text(new, reply_markup=None)
    except Exception:
        pass
    await call.answer("Tasdiqlandi ✅")


@dp.callback_query(F.data.startswith("no:"))
async def reject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Faqat admin uchun.", show_alert=True)
    try:
        uid = int(call.data.split(":")[1])
    except (ValueError, IndexError):
        return await call.answer("Xato.", show_alert=True)

    row = get_user(uid)
    await send_core(uid, "rejected", row)
    # Qayta chek yubora olishi uchun bosqichni "chek kutish"ga qaytaramiz
    mark(uid, stage="paid_click", submitted_at=None)
    try:
        base = call.message.caption if call.message.caption is not None else call.message.text
        new = (base or "") + "\n\n❌ RAD ETILDI"
        if call.message.caption is not None:
            await call.message.edit_caption(caption=new, reply_markup=None)
        else:
            await call.message.edit_text(new, reply_markup=None)
    except Exception:
        pass
    await call.answer("Rad etildi.")


# --------------------------------------------------------------------------
# 5-QISM: ADMIN PANELI
# --------------------------------------------------------------------------

class Adm(StatesGroup):
    msg_text = State()
    msg_button = State()
    setting = State()
    promo_add = State()
    t_time = State()       # timed vaqti
    t_content = State()    # timed matn/media
    t_button = State()     # timed tugma matni
    broadcast = State()


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Xabar va tugmalar", callback_data="msgs")],
        [InlineKeyboardButton(text="🔁 Qayta jalb (retarget)", callback_data="rt")],
        [InlineKeyboardButton(text="📅 Rejalashtirilgan xabarlar", callback_data="sc")],
        [InlineKeyboardButton(text="🎟 Promo kodlar", callback_data="promos")],
        [InlineKeyboardButton(text="⚙️ Narx sozlamasi", callback_data="cfg")],
        [InlineKeyboardButton(text="📢 Hammaga xabar", callback_data="bcast")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
    ])


def back_kb(target: str = "menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=target)
    ]])


@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🔧 <b>Admin panel</b>", reply_markup=admin_menu())


@dp.message(Command("bekor"))
async def cancel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_menu())


@dp.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.answer("🔧 <b>Admin panel</b>", reply_markup=admin_menu())
    await call.answer()


# ---------- 5.1 Statistika ----------
@dp.callback_query(F.data == "stats")
async def cb_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    s = stats()
    await call.message.answer(
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchi: <b>{s['jami']}</b>\n"
        f"✅ Ro'yxatdan o'tgan: <b>{s['reg']}</b>\n"
        f"🧾 To'lov yuborgan: <b>{s['sub']}</b>\n"
        f"🎉 Tasdiqlangan (sotib olgan): <b>{s['sotib']}</b>\n"
        f"🎟 Promo ishlatilgan: <b>{s['promo']}</b>",
        reply_markup=back_kb(),
    )
    await call.answer()


# ---------- 5.2 Oqim xabarlari ----------
@dp.callback_query(F.data == "msgs")
async def cb_msgs(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    rows = [[InlineKeyboardButton(
        text=f"{'✅' if m['enabled'] else '🚫'} {m['title']}",
        callback_data=f"m:{m['key']}")] for m in all_messages()]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu")])
    await call.message.answer(
        "💬 <b>Xabar va tugmalar</b>\n\n"
        "Oqim tartibida. Tahrirlash uchun xabarni tanlang.\n"
        "ℹ️ Matnda <code>{ism}</code> yozsangiz — foydalanuvchi ismi qo'yiladi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await call.answer()


def msg_card(key: str) -> tuple[str, InlineKeyboardMarkup]:
    m = get_message(key)
    tur = MEDIA_LABEL.get(m["media_type"] or "", "matn")
    btn = m["button_text"] or "— tugma yo'q —"
    holat = "✅ yoqilgan" if m["enabled"] else "🚫 o'chirilgan"
    matn = preview(m["text"]) or "(bo'sh)"
    text = (
        f"<b>{m['title']}</b>\n"
        f"Holati: {holat}  |  Turi: {tur}\n\n"
        f"<b>Matn:</b>\n{matn}\n\n"
        f"<b>Tugma:</b> {html_lib.escape(btn)}"
    )
    rows = [[InlineKeyboardButton(text="✏️ Matn / media", callback_data=f"mt:{key}")]]
    if key in CORE_BUTTON_CB:
        rows.append([InlineKeyboardButton(text="🔘 Tugma matni", callback_data=f"mb:{key}")])
    rows.append([InlineKeyboardButton(
        text="🚫 O'chirib qo'yish" if m["enabled"] else "✅ Yoqish",
        callback_data=f"mo:{key}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="msgs")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query(F.data.startswith("m:"))
async def cb_msg_one(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    text, kb = msg_card(call.data.split(":", 1)[1])
    await call.message.answer(text, reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data.startswith("mo:"))
async def cb_msg_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    key = call.data.split(":", 1)[1]
    m = get_message(key)
    update_message(key, enabled=0 if m["enabled"] else 1)
    text, kb = msg_card(key)
    await call.message.answer(text, reply_markup=kb)
    await call.answer("O'zgartirildi")


@dp.callback_query(F.data.startswith("mt:"))
async def cb_msg_text(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    key = call.data.split(":", 1)[1]
    await state.update_data(key=key)
    await state.set_state(Adm.msg_text)
    await call.message.answer(
        "✏️ Yangi <b>matn</b> yuboring.\n\n"
        "ℹ️ Rasm, video, ovozli xabar, yumaloq video yoki fayl ham yubora olasiz — "
        "izohi (caption) matn bo'lib qoladi.\n"
        "ℹ️ Mediani olib tashlash uchun oddiy matn yuboring.\n"
        "ℹ️ <code>{ism}</code> — foydalanuvchi ismi.\n\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.msg_text)
async def save_msg_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    key = (await state.get_data())["key"]
    media_type, file_id, text = extract_media(message)
    if not text and not file_id:
        return await message.answer("❌ Bo'sh. Matn yoki media yuboring.\n(Bekor: /bekor)")
    update_message(key, text=text, media_type=media_type, file_id=file_id)
    await state.clear()
    card, kb = msg_card(key)
    await message.answer("✅ Saqlandi!\n\n" + card, reply_markup=kb)


@dp.callback_query(F.data.startswith("mb:"))
async def cb_msg_button(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    key = call.data.split(":", 1)[1]
    await state.update_data(key=key)
    await state.set_state(Adm.msg_button)
    await call.message.answer(
        "🔘 Tugmaning yangi matnini yuboring.\n\n"
        "Tugmani olib tashlash uchun <code>-</code> yuboring.\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.msg_button)
async def save_msg_button(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    key = (await state.get_data())["key"]
    yangi = (message.text or "").strip()
    update_message(key, button_text="" if yangi == "-" else yangi)
    await state.clear()
    card, kb = msg_card(key)
    await message.answer("✅ Saqlandi!\n\n" + card, reply_markup=kb)


# ---------- 5.3 Narx sozlamasi ----------
@dp.callback_query(F.data == "cfg")
async def cb_cfg(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await state.update_data(key="price")
    await state.set_state(Adm.setting)
    await call.message.answer(
        f"⚙️ <b>Kurs narxi</b>\n\n"
        f"Hozirgi: <b>{get_int('price')} so'm</b> "
        f"(0 = adminga hisob-kitobda ko'rsatilmaydi)\n\n"
        f"Yangi narxni faqat <b>raqam</b> bilan yuboring. Masalan: <code>480000</code>\n"
        f"(Bekor: /bekor)",
        reply_markup=back_kb(),
    )
    await call.answer()


@dp.message(Adm.setting)
async def save_cfg(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip().replace(" ", "")
    if not raw.isdigit():
        return await message.answer("❌ Faqat raqam. Masalan: <code>480000</code>\n(Bekor: /bekor)")
    set_setting("price", raw)
    await state.clear()
    await message.answer(f"✅ Narx: <b>{fmt(int(raw))} so'm</b>", reply_markup=admin_menu())


# ---------- 5.4 Promo kodlar ----------
@dp.callback_query(F.data == "promos")
async def cb_promos(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    promos = list_promos()
    now = int(time.time())
    if promos:
        satrlar = ["🎟 <b>Promo kodlar</b>\n"]
        for code, disc, exp, soni in promos:
            if exp is None:
                muddat = "muddatsiz"
            elif exp < now:
                muddat = "⛔ muddati o'tgan"
            else:
                qolgan = (exp - now) // 86400
                muddat = f"{qolgan} kun qoldi"
            satrlar.append(f"<b>{code}</b> — {disc}% — {muddat} — {soni} ta ishlatgan")
        text = "\n".join(satrlar) + "\n\nO'chirish uchun kodni bosing."
    else:
        text = "🎟 Hozircha promo kod yo'q."

    rows = [[InlineKeyboardButton(text=f"🗑 {c} ({d}%)", callback_data=f"pd:{c}")]
            for c, d, e, n in promos]
    rows.append([InlineKeyboardButton(text="➕ Promo qo'shish", callback_data="pa")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu")])
    await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@dp.callback_query(F.data == "pa")
async def cb_promo_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(Adm.promo_add)
    await call.message.answer(
        "➕ <b>Yangi promo kod</b>\n\n"
        "Format: <code>KOD FOIZ [KUN]</code>\n\n"
        "• <code>IYUL 40</code> — 40% chegirma, muddatsiz\n"
        "• <code>IYUL 40 7</code> — 40% chegirma, 7 kun amal qiladi\n\n"
        "ℹ️ Promo faqat chek yuborilganda, uning izohida yozilsa ishlaydi.\n"
        "(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.promo_add)
async def save_promo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        return await message.answer(
            "❌ Format: <code>KOD FOIZ [KUN]</code>\nMasalan: <code>IYUL 40 7</code>\n(Bekor: /bekor)")
    code = parts[0]
    percent = int(parts[1])
    days = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 0
    if not (1 <= percent <= 99):
        return await message.answer("❌ Foiz 1–99 orasida bo'lsin.\n(Bekor: /bekor)")
    add_promo(code, percent, days)
    await state.clear()
    muddat = f"{days} kun amal qiladi" if days > 0 else "muddatsiz"
    await message.answer(
        f"✅ Promo qo'shildi!\n\n🎟 <b>{code.upper()}</b> — {percent}% — {muddat}",
        reply_markup=admin_menu(),
    )


@dp.callback_query(F.data.startswith("pd:"))
async def cb_promo_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    code = call.data.split(":", 1)[1]
    delete_promo(code)
    await call.message.answer(f"🗑 <b>{code}</b> o'chirildi.", reply_markup=admin_menu())
    await call.answer()


# ---------- 5.5 Vaqtli xabarlar (retarget + rejalashtirilgan) ----------
ANCHOR_LABEL = {
    "start": "start bosilgandan keyin",
    "register": "ro'yxatdan o'tgandan keyin",
    "paid": "sotib olgandan keyin",
}


def timed_list_ui(kind: str) -> tuple[str, InlineKeyboardMarkup]:
    items = list_timed(kind)
    rows = [[InlineKeyboardButton(
        text=f"{'✅' if c['enabled'] else '🚫'} {c['after_minutes']} min — "
             f"{(c['text'] or '(media)')[:22]}",
        callback_data=f"t:{c['id']}")] for c in items]
    if kind == "retarget":
        rows.append([InlineKeyboardButton(text="➕ Yangi retarget", callback_data="ta:retarget:start")])
        title = ("🔁 <b>Qayta jalb (retarget)</b>\n\n"
                 "Vaqt <b>/start</b> bosilgandan hisoblanadi. Foydalanuvchi ism+raqamini "
                 "yuborsa — bular to'xtaydi.\nHar bir tugma to'lov ma'lumotiga qaytaradi.\n"
                 "ℹ️ <code>{ism}</code> — foydalanuvchi ismi.")
    else:
        rows.append([InlineKeyboardButton(text="➕ Ro'yxatdan keyin", callback_data="ta:sched:register")])
        rows.append([InlineKeyboardButton(text="➕ Sotib olgandan keyin", callback_data="ta:sched:paid")])
        title = ("📅 <b>Rejalashtirilgan xabarlar</b>\n\n"
                 "Ro'yxatdan o'tgan yoki sotib olgan foydalanuvchiga belgilangan "
                 "vaqtdan keyin avtomat yuboriladi.")
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu")])
    if not items:
        title += "\n\nHozircha bitta ham yo'q."
    return title, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query(F.data == "rt")
async def cb_rt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    title, kb = timed_list_ui("retarget")
    await call.message.answer(title, reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data == "sc")
async def cb_sc(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    title, kb = timed_list_ui("sched")
    await call.message.answer(title, reply_markup=kb)
    await call.answer()


def timed_card(tid: int) -> tuple[str, InlineKeyboardMarkup]:
    c = get_timed(tid)
    tur = MEDIA_LABEL.get(c["media_type"] or "", "matn")
    anchor = ANCHOR_LABEL.get(c["anchor"], c["anchor"])
    back = "rt" if c["kind"] == "retarget" else "sc"
    btn = c["button_text"] or "— yo'q —"
    text = (
        f"{'🔁' if c['kind']=='retarget' else '📅'} <b>Vaqtli xabar</b>\n\n"
        f"⏱ Vaqt: <b>{c['after_minutes']} minut</b> ({anchor})\n"
        f"Holati: {'✅ yoqilgan' if c['enabled'] else '🚫 o‘chirilgan'}  |  Turi: {tur}\n"
        f"📨 Yuborilgan: <b>{timed_receivers(tid)}</b> ta odamga\n"
    )
    if c["kind"] == "retarget":
        text += f"🔘 Tugma: {html_lib.escape(btn)}\n"
    text += f"\n<b>Matn:</b>\n{preview(c['text']) or '(media/bo‘sh)'}"

    rows = [
        [InlineKeyboardButton(text="⏱ Vaqt", callback_data=f"tt:{tid}")],
        [InlineKeyboardButton(text="✏️ Matn / media", callback_data=f"tx:{tid}")],
    ]
    if c["kind"] == "retarget":
        rows.append([InlineKeyboardButton(text="🔘 Tugma matni", callback_data=f"tb:{tid}")])
    rows.append([InlineKeyboardButton(
        text="🚫 O'chirib qo'yish" if c["enabled"] else "✅ Yoqish",
        callback_data=f"to:{tid}")])
    rows.append([InlineKeyboardButton(text="🗑 Butunlay o'chirish", callback_data=f"td:{tid}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back)])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query(F.data.startswith("t:"))
async def cb_timed_one(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    tid = int(call.data.split(":", 1)[1])
    if not get_timed(tid):
        return await call.answer("Topilmadi.", show_alert=True)
    text, kb = timed_card(tid)
    await call.message.answer(text, reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data.startswith("to:"))
async def cb_timed_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    tid = int(call.data.split(":", 1)[1])
    c = get_timed(tid)
    if not c:
        return await call.answer("Topilmadi.", show_alert=True)
    update_timed(tid, enabled=0 if c["enabled"] else 1)
    text, kb = timed_card(tid)
    await call.message.answer(text, reply_markup=kb)
    await call.answer("O'zgartirildi")


@dp.callback_query(F.data.startswith("td:"))
async def cb_timed_delete(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    tid = int(call.data.split(":", 1)[1])
    c = get_timed(tid)
    back = "rt" if (c and c["kind"] == "retarget") else "sc"
    delete_timed(tid)
    title, kb = timed_list_ui("retarget" if back == "rt" else "sched")
    await call.message.answer("🗑 O'chirildi.\n\n" + title, reply_markup=kb)
    await call.answer()


# --- Yangi qo'shish: ta:<kind>:<anchor> ---
@dp.callback_query(F.data.startswith("ta:"))
async def cb_timed_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    _, kind, anchor = call.data.split(":")
    await state.set_state(Adm.t_time)
    await state.update_data(kind=kind, anchor=anchor, tid=None)
    await call.message.answer(
        f"⏱ Xabar <b>{ANCHOR_LABEL.get(anchor, anchor)}</b> necha minut o'tib yuborilsin?\n\n"
        "Faqat raqam. Masalan:\n<code>7</code>, <code>60</code> (1 soat), "
        "<code>1440</code> (1 kun)\n\n(Bekor: /bekor)"
    )
    await call.answer()


# --- Vaqtni o'zgartirish: tt:<id> ---
@dp.callback_query(F.data.startswith("tt:"))
async def cb_timed_time(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    tid = int(call.data.split(":", 1)[1])
    c = get_timed(tid)
    if not c:
        return await call.answer("Topilmadi.", show_alert=True)
    await state.set_state(Adm.t_time)
    await state.update_data(kind=c["kind"], anchor=c["anchor"], tid=tid)
    await call.message.answer(
        f"⏱ Hozirgi: <b>{c['after_minutes']} minut</b>\n\n"
        "Yangi qiymatni faqat raqam bilan yuboring.\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.t_time)
async def save_timed_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        return await message.answer("❌ 0 dan katta butun raqam. Masalan: <code>7</code>\n(Bekor: /bekor)")
    data = await state.get_data()
    tid = data.get("tid")
    if tid:
        update_timed(tid, after_minutes=int(raw))
        await state.clear()
        text, kb = timed_card(tid)
        return await message.answer("✅ Vaqt yangilandi!\n\n" + text, reply_markup=kb)
    # Yangi: vaqtni saqlab, matn/media so'raymiz
    await state.update_data(minutes=int(raw))
    await state.set_state(Adm.t_content)
    await message.answer(
        f"✅ Vaqt: <b>{int(raw)} minut</b>\n\n"
        "Endi xabar <b>matni/mediasini</b> yuboring.\n\n"
        "ℹ️ Rasm, video, ovozli xabar, yumaloq video, fayl — istalgan turda.\n"
        "ℹ️ <code>{ism}</code> — foydalanuvchi ismi.\n(Bekor: /bekor)"
    )


# --- Matn/media o'zgartirish: tx:<id> ---
@dp.callback_query(F.data.startswith("tx:"))
async def cb_timed_content(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    tid = int(call.data.split(":", 1)[1])
    if not get_timed(tid):
        return await call.answer("Topilmadi.", show_alert=True)
    await state.set_state(Adm.t_content)
    await state.update_data(tid=tid, minutes=None)
    await call.message.answer(
        "✏️ Yangi matn/mediani yuboring (rasm/video/ovozli/yumaloq video/fayl).\n"
        "ℹ️ <code>{ism}</code> — foydalanuvchi ismi.\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.t_content)
async def save_timed_content(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    media_type, file_id, text = extract_media(message)
    if not text and not file_id:
        return await message.answer("❌ Bo'sh. Matn yoki media yuboring.\n(Bekor: /bekor)")
    data = await state.get_data()
    tid = data.get("tid")
    if tid:
        update_timed(tid, text=text, media_type=media_type, file_id=file_id)
        await state.clear()
        card, kb = timed_card(tid)
        return await message.answer("✅ Saqlandi!\n\n" + card, reply_markup=kb)

    # Yangi xabar yaratish
    kind = data["kind"]
    anchor = data["anchor"]
    minutes = data["minutes"]
    if kind == "retarget":
        # Retargetga tugma matni ham so'raymiz
        await state.update_data(text=text, media_type=media_type, file_id=file_id)
        await state.set_state(Adm.t_button)
        return await message.answer(
            "🔘 Endi tugma matnini yuboring (to'lovga qaytaruvchi tugma).\n\n"
            "Tugmasiz bo'lsin desangiz <code>-</code> yuboring.\n(Bekor: /bekor)"
        )
    tid = add_timed(kind, anchor, minutes, text, media_type, file_id, "")
    await state.clear()
    card, kb = timed_card(tid)
    await message.answer("✅ Qo'shildi!\n\n" + card, reply_markup=kb)


# --- Retarget tugma matni: tb:<id> yoki yangi retarget yaratishda ---
@dp.callback_query(F.data.startswith("tb:"))
async def cb_timed_button(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    tid = int(call.data.split(":", 1)[1])
    if not get_timed(tid):
        return await call.answer("Topilmadi.", show_alert=True)
    await state.set_state(Adm.t_button)
    await state.update_data(tid=tid)
    await call.message.answer(
        "🔘 Tugmaning yangi matnini yuboring.\n\n"
        "Tugmani olib tashlash uchun <code>-</code> yuboring.\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.t_button)
async def save_timed_button(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    yangi = (message.text or "").strip()
    btn = "" if yangi == "-" else yangi
    data = await state.get_data()
    tid = data.get("tid")
    if tid:
        update_timed(tid, button_text=btn)
        await state.clear()
        card, kb = timed_card(tid)
        return await message.answer("✅ Saqlandi!\n\n" + card, reply_markup=kb)
    # Yangi retarget yaratishning oxirgi bosqichi
    tid = add_timed("retarget", data["anchor"], data["minutes"],
                    data.get("text", ""), data.get("media_type", ""),
                    data.get("file_id", ""), btn)
    await state.clear()
    card, kb = timed_card(tid)
    await message.answer("✅ Qo'shildi!\n\n" + card, reply_markup=kb)


# ---------- 5.6 Broadcast ----------
@dp.callback_query(F.data == "bcast")
async def cb_bcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(Adm.broadcast)
    await call.message.answer(
        f"📢 Barcha <b>{len(all_user_ids())}</b> ta foydalanuvchiga yuboriladigan "
        "xabarni yuboring.\n\nℹ️ Matn, rasm, video, fayl — istalgan turda.\n(Bekor: /bekor)"
    )
    await call.answer()


@dp.message(Adm.broadcast)
async def do_bcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    ids = all_user_ids()
    await message.answer(f"Yuborilyapti... ({len(ids)} ta)")
    sent = failed = 0
    for uid in ids:
        try:
            await bot.copy_message(uid, message.chat.id, message.message_id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer(
        f"✅ Yuborildi: <b>{sent}</b>\n❌ Yetib bormadi: <b>{failed}</b>",
        reply_markup=admin_menu(),
    )


# --------------------------------------------------------------------------
# 5.7 ENG OXIRGI HANDLER — tanilmagan tugmalar (ENG OXIRIDA turishi SHART)
# --------------------------------------------------------------------------
@dp.callback_query()
async def on_unknown_callback(call: CallbackQuery):
    logging.warning("❓ Tanilmagan tugma: data=%r user=%s", call.data, call.from_user.id)
    try:
        await call.answer("Bu tugma eskirgan. /start bosib qaytadan boshlang.", show_alert=True)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 6-QISM: FONDAGI REJALASHTIRUVCHI
# --------------------------------------------------------------------------

async def process_timed():
    """Vaqti kelgan retarget/rejalashtirilgan xabarlarni yuboradi (xatoga chidamli)."""
    items = [t for t in list_timed() if t["enabled"]]
    if not items:
        return

    now = int(time.time())
    con = db(); cur = con.cursor()
    cur.execute(
        "SELECT user_id, started_at, registered_at, paid_at FROM users"
    )
    users = cur.fetchall()
    cur.execute("SELECT timed_id, user_id FROM timed_sent")
    sent = {(r[0], r[1]) for r in cur.fetchall()}
    con.close()

    for u in users:
        uid = u["user_id"]
        if is_admin(uid):
            continue
        urow = get_user(uid)   # to'liq qator (stage/enrolled/discount ...)
        for t in items:
            tid = t["id"]
            if (tid, uid) in sent:
                continue

            anchor = t["anchor"]
            if anchor == "start":
                base = u["started_at"]
            elif anchor == "register":
                base = u["registered_at"]
            elif anchor == "paid":
                base = u["paid_at"]
            else:
                base = None
            if not base:
                continue
            if now - base < t["after_minutes"] * 60:
                continue

            # Gating (yuborishga hojat yo'q bo'lsa — belgilab, o'tkazib yuboramiz)
            if t["kind"] == "retarget" and funnel_done(urow):
                mark_timed_sent(tid, uid)
                continue
            if anchor == "register" and is_enrolled(urow):
                mark_timed_sent(tid, uid)
                continue

            kb = retarget_kb(t) if t["kind"] == "retarget" else None
            try:
                res = await deliver(uid, t["text"], t["media_type"], t["file_id"], kb, urow)
            except TelegramForbiddenError:
                # Foydalanuvchi botni bloklagan — qayta urinmaymiz
                mark_timed_sent(tid, uid)
                logging.info("⛔ Bloklangan, o'tkazildi: user=%s timed=%s", uid, tid)
                continue
            except Exception as e:
                logging.exception("process_timed send: %s", e)
                res = None

            if res is not None:
                mark_timed_sent(tid, uid)
                logging.info("📨 Timed yuborildi: user=%s timed=%s (%s)", uid, tid, t["kind"])
            else:
                logging.warning("Timed yuborilmadi (qayta urinamiz): user=%s timed=%s", uid, tid)
            await asyncio.sleep(0.05)


async def scheduler_loop():
    """Har 30 soniyada vaqti kelgan xabarlarni tekshiradi."""
    while True:
        try:
            await process_timed()
        except Exception as e:
            logging.exception("scheduler_loop: %s", e)
        await asyncio.sleep(30)


# --------------------------------------------------------------------------
# 7-QISM: ISHGA TUSHIRISH
# --------------------------------------------------------------------------
async def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN topilmadi (.env faylini tekshiring).")
    if not ADMIN_ID:
        logging.warning("⚠️ ADMIN_ID belgilanmagan — admin panel ishlamaydi.")
    init_db()
    logging.info("✅ Bot ishga tushdi.")
    asyncio.create_task(scheduler_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
