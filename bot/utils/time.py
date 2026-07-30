"""Vaqt bilan ishlash: bazada hamma narsa UTC, ko'rsatishda Asia/Tashkent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.config import get_settings

UTC = timezone.utc


def utcnow() -> datetime:
    """Hozirgi vaqt — timezone-aware UTC."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Naive datetime'ni UTC deb qabul qiladi, aware bo'lsa UTC'ga o'giradi.

    SQLite `DateTime(timezone=True)` ni naive qilib qaytaradi, shuning uchun
    bazadan o'qilgan har qanday vaqt shu funksiyadan o'tkaziladi.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_local(value: datetime) -> datetime:
    """UTC vaqtni admin ko'radigan mahalliy vaqtga (Asia/Tashkent) o'giradi."""
    return ensure_utc(value).astimezone(get_settings().timezone)


def fmt(value: datetime | None, with_seconds: bool = False) -> str:
    """Adminga ko'rsatish uchun formatlangan mahalliy vaqt."""
    if value is None:
        return "—"
    pattern = "%d.%m.%Y %H:%M:%S" if with_seconds else "%d.%m.%Y %H:%M"
    return to_local(value).strftime(pattern)


def in_minutes(minutes: float) -> datetime:
    """Hozirdan `minutes` daqiqa keyingi UTC vaqt."""
    return utcnow() + timedelta(minutes=minutes)


def humanize_delta(delta: timedelta) -> str:
    """`2 soat 5 daqiqa` ko'rinishidagi qisqa matn."""
    total = int(delta.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} kun")
    if hours:
        parts.append(f"{hours} soat")
    if minutes:
        parts.append(f"{minutes} daqiqa")
    if not parts:
        parts.append(f"{seconds} soniya")
    return sign + " ".join(parts)
