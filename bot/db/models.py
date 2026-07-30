"""SQLAlchemy 2.0 modellari.

Qoidalar:
* Barcha vaqtlar bazada **UTC** da saqlanadi (`DateTime(timezone=True)`).
* Enum'lar `String` sifatida saqlanadi — SQLite ↔ PostgreSQL ko'chishi oson bo'lsin.
* Har bir foydalanuvchiga tegishli yozuv `users.id` ga FK bilan bog'lanadi.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from bot.utils.time import utcnow


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON}


def _ts_column(**kwargs: Any) -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), **kwargs)


# --------------------------------------------------------------------------
# Konstantalar (String sifatida saqlanadigan "enum"lar)
# --------------------------------------------------------------------------


class FunnelStatus:
    """Foydalanuvchining voronkadagi holati."""

    NEW = "new"                      # /start bosgan
    REGISTERED = "registered"        # "Ro'yxatdan o'tish" bosilgan
    WAITING_RECEIPT = "waiting_receipt"    # "To'lov qildim" bosilgan, chek kutilmoqda
    WAITING_CONTACT = "waiting_contact"    # chek kelgan, ism/telefon kutilmoqda
    PENDING_REVIEW = "pending_review"      # admin qaroriga yuborilgan
    APPROVED = "approved"            # to'lov tasdiqlangan
    REJECTED = "rejected"            # rad etilgan (yana waiting_receipt ga qaytadi)
    COLD = "cold"                    # zanjir tugagan, javob yo'q

    ALL = (NEW, REGISTERED, WAITING_RECEIPT, WAITING_CONTACT,
           PENDING_REVIEW, APPROVED, REJECTED, COLD)

    #: Eslatma zanjiri faqat shu holatlarda davom etadi
    REMINDABLE = (NEW, REGISTERED, COLD)


class TaskStatus:
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskType:
    REMINDER = "reminder"              # 1–4 eslatma zanjiri
    SCHEDULED = "scheduled"            # admin yaratgan rejalashtirilgan xabar
    BROADCAST = "broadcast"            # ommaviy yuborish


class PaymentStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DiscountType:
    PERCENT = "percent"
    FIXED = "fixed"


class Anchor:
    """Rejalashtirilgan xabar uchun boshlanish nuqtasi."""

    REGISTERED = "registered"          # ro'yxatdan o'tgan vaqt
    APPROVED = "approved"              # to'lov tasdiqlangan vaqt


class Segment:
    ALL = "all"
    PAID = "paid"
    UNPAID = "unpaid"
    COLD = "cold"


class MediaType:
    NONE = ""
    PHOTO = "photo"
    VOICE = "voice"
    AUDIO = "audio"
    VIDEO = "video"
    VIDEO_NOTE = "video_note"
    DOCUMENT = "document"
    ANIMATION = "animation"

    ALL = (PHOTO, VOICE, AUDIO, VIDEO, VIDEO_NOTE, DOCUMENT, ANIMATION)


# --------------------------------------------------------------------------
# Jadvallar
# --------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))

    # Foydalanuvchi o'zi yuborgan ism-familiya va telefon
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))

    funnel_status: Mapped[str] = mapped_column(String(32), default=FunnelStatus.NEW, index=True)
    #: Yuborilgan oxirgi eslatma raqami (0 = hali yo'q). Faqat oldinga yuradi.
    reminder_index: Mapped[int] = mapped_column(Integer, default=0)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = _ts_column(default=utcnow)
    registered_at: Mapped[datetime | None] = _ts_column()   # "Ro'yxatdan o'tish" bosilgan
    approved_at: Mapped[datetime | None] = _ts_column()      # to'lov tasdiqlangan
    last_action_at: Mapped[datetime | None] = _ts_column()
    blocked_at: Mapped[datetime | None] = _ts_column()

    payments: Mapped[list["Payment"]] = relationship(back_populates="user", lazy="selectin")

    @property
    def display_name(self) -> str:
        return (self.full_name or " ".join(filter(None, [self.first_name, self.last_name])) or "").strip()

    @property
    def tg_link(self) -> str:
        return f"@{self.username}" if self.username else f"id{self.telegram_id}"


class Content(Base):
    """Bot yuboradigan har bir xabar — matn, media va tugma matni."""

    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128), default="")        # admin ko'radigan nom
    group: Mapped[str] = mapped_column(String(32), default="main")     # main / reminder / error / promo
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    hint: Mapped[str] = mapped_column(String(255), default="")         # admin uchun izoh

    text: Mapped[str] = mapped_column(Text, default="")
    parse_mode: Mapped[str] = mapped_column(String(16), default="HTML")
    media_type: Mapped[str] = mapped_column(String(16), default=MediaType.NONE)
    file_id: Mapped[str] = mapped_column(Text, default="")
    button_text: Mapped[str] = mapped_column(String(128), default="")
    button_url: Mapped[str] = mapped_column(Text, default="")          # bo'sh bo'lsa — callback tugma
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[datetime] = _ts_column(default=utcnow, onupdate=utcnow)
    updated_by: Mapped[int | None] = mapped_column(BigInteger)


class Setting(Base):
    """Kalit-qiymat sozlamalar: eslatma kechikishlari, narx, zaxira ism va h.k."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = _ts_column(default=utcnow, onupdate=utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    file_id: Mapped[str] = mapped_column(Text, default="")
    file_type: Mapped[str] = mapped_column(String(16), default=MediaType.PHOTO)
    caption: Mapped[str] = mapped_column(Text, default="")

    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))

    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id", ondelete="SET NULL"))
    promo_code_text: Mapped[str] = mapped_column(String(64), default="")
    base_price: Mapped[int] = mapped_column(Integer, default=0)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    final_price: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(16), default=PaymentStatus.PENDING, index=True)
    decided_by: Mapped[int | None] = mapped_column(BigInteger)     # admin telegram_id
    decided_by_name: Mapped[str] = mapped_column(String(255), default="")
    decided_at: Mapped[datetime | None] = _ts_column()

    #: Adminlarga yuborilgan xabarlar: [{"chat_id": 1, "message_id": 2}, ...]
    admin_messages: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = _ts_column(default=utcnow, index=True)

    user: Mapped[User] = relationship(back_populates="payments", lazy="joined")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(16), default=DiscountType.PERCENT)
    value: Mapped[int] = mapped_column(Integer, default=0)          # foiz yoki so'm
    usage_limit: Mapped[int] = mapped_column(Integer, default=0)     # 0 = cheksiz
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime | None] = _ts_column()
    expires_at: Mapped[datetime | None] = _ts_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _ts_column(default=utcnow)
    created_by: Mapped[int | None] = mapped_column(BigInteger)

    usages: Mapped[list["PromoUsage"]] = relationship(back_populates="promo", lazy="selectin")


class PromoUsage(Base):
    __tablename__ = "promo_usages"
    __table_args__ = (
        UniqueConstraint("promo_code_id", "user_id", name="uq_promo_usage_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"))
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    final_price: Mapped[int] = mapped_column(Integer, default=0)
    used_at: Mapped[datetime] = _ts_column(default=utcnow)

    promo: Mapped[PromoCode] = relationship(back_populates="usages", lazy="joined")


class ScheduledTask(Base):
    """Rejalashtirilgan har bir yuborish — restartdan keyin ham tiklanadi."""

    __tablename__ = "scheduled_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_type", "dedup_key", name="uq_task_dedup"),
        Index("ix_tasks_due", "status", "run_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_type: Mapped[str] = mapped_column(String(24), index=True)
    #: Idempotentlik kaliti: reminder uchun "1".."4", scheduled uchun "tpl:<id>",
    #: broadcast uchun "bc:<id>".
    dedup_key: Mapped[str] = mapped_column(String(64))
    chain_index: Mapped[int] = mapped_column(Integer, default=0)

    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    run_at: Mapped[datetime] = _ts_column(index=True)
    status: Mapped[str] = mapped_column(String(16), default=TaskStatus.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime | None] = _ts_column()
    claimed_at: Mapped[datetime | None] = _ts_column()

    created_at: Mapped[datetime] = _ts_column(default=utcnow)

    user: Mapped[User] = relationship(lazy="joined")


class ScheduledTemplate(Base):
    """Admin yaratgan rejalashtirilgan xabar shabloni."""

    __tablename__ = "scheduled_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    anchor: Mapped[str] = mapped_column(String(24), default=Anchor.APPROVED)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=60)

    text: Mapped[str] = mapped_column(Text, default="")
    parse_mode: Mapped[str] = mapped_column(String(16), default="HTML")
    media_type: Mapped[str] = mapped_column(String(16), default=MediaType.NONE)
    file_id: Mapped[str] = mapped_column(Text, default="")
    button_text: Mapped[str] = mapped_column(String(128), default="")
    button_url: Mapped[str] = mapped_column(Text, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _ts_column(default=utcnow)
    created_by: Mapped[int | None] = mapped_column(BigInteger)


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    segment: Mapped[str] = mapped_column(String(24), default=Segment.ALL)
    text: Mapped[str] = mapped_column(Text, default="")
    parse_mode: Mapped[str] = mapped_column(String(16), default="HTML")
    media_type: Mapped[str] = mapped_column(String(16), default=MediaType.NONE)
    file_id: Mapped[str] = mapped_column(Text, default="")
    button_text: Mapped[str] = mapped_column(String(128), default="")
    button_url: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[str] = mapped_column(String(16), default="running")   # running / done
    total: Mapped[int] = mapped_column(Integer, default=0)
    delivered: Mapped[int] = mapped_column(Integer, default=0)
    blocked: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = _ts_column(default=utcnow)
    finished_at: Mapped[datetime | None] = _ts_column()


class ReminderClick(Base):
    """Qaysi eslatmadan keyin foydalanuvchi qaytgani — konversiya statistikasi."""

    __tablename__ = "reminder_clicks"
    __table_args__ = (
        UniqueConstraint("user_id", "reminder_index", name="uq_reminder_click"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reminder_index: Mapped[int] = mapped_column(Integer)
    clicked_at: Mapped[datetime] = _ts_column(default=utcnow)


class ErrorLog(Base):
    """Oxirgi xatolar — `/health` va diagnostika uchun."""

    __tablename__ = "error_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    traceback: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = _ts_column(default=utcnow, index=True)
