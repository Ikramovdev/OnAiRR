"""Loyiha sozlamalari — .env fayldan o'qiladi (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}",
        alias="DATABASE_URL",
    )
    tz: str = Field(default="Asia/Tashkent", alias="TZ")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Path = Field(default=BASE_DIR / "logs" / "bot.log", alias="LOG_FILE")

    # Scheduler
    scheduler_poll_seconds: int = Field(default=10, alias="SCHEDULER_POLL_SECONDS")
    scheduler_batch_size: int = Field(default=100, alias="SCHEDULER_BATCH_SIZE")

    # Yuborish limitlari (Telegram: ~30 msg/sek global, 1 msg/sek bitta chatga)
    global_rate_limit: int = Field(default=25, alias="GLOBAL_RATE_LIMIT")
    max_send_attempts: int = Field(default=5, alias="MAX_SEND_ATTEMPTS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> list[int]:
        """`ADMIN_IDS=123,456` ko'rinishidagi qatorni ro'yxatga aylantiradi."""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(part.strip()) for part in value.replace(";", ",").split(",") if part.strip()]
        if isinstance(value, (list, tuple)):
            return [int(item) for item in value]
        raise ValueError("ADMIN_IDS noto'g'ri formatda")

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
