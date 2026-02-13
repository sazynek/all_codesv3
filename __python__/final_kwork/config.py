"""
Конфигурация проекта с использованием pydantic-settings.

Поддерживает:
- Валидацию переменных окружения
- Типизацию
- Значения по умолчанию
- .env.example файлы
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Все значения загружаются из переменных окружения или .env.example файла.
    """

    model_config = SettingsConfigDict(
        env_file=".env.example",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Telegram API ===
    tg_api_id: int = Field(default=0, description="Telegram API ID")
    tg_api_hash: str = Field(default="", description="Telegram API Hash")
    tg_bot_token: str = Field(default="", description="Bot token from @BotFather")

    # === Database ===
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data.db", description="SQLAlchemy database URL"
    )

    # === Admin IDs ===
    admin_ids: str = Field(
        default="", description="Comma-separated list of admin Telegram IDs"
    )

    # === Security ===
    max_accounts_per_manager: int = Field(
        default=3, ge=1, le=10, description="Maximum active accounts per manager"
    )
    max_requests_per_day: int = Field(
        default=3, ge=1, le=50, description="Maximum requests per 24 hours (anti-spam)"
    )
    request_cooldown_seconds: int = Field(
        default=60,
        ge=0,
        le=300,
        description="Cooldown between account requests (seconds)",
    )

    # === Telethon workers ===
    code_wait_timeout: int = Field(
        default=180,
        ge=30,
        le=600,
        description="Timeout for waiting confirmation code (seconds)",
    )

    # === Telethon connection settings ===
    connection_retries: int = Field(
        default=5, ge=1, le=20, description="Number of connection retry attempts"
    )
    request_retries: int = Field(
        default=5, ge=1, le=10, description="Number of request retry attempts"
    )
    retry_delay: int = Field(
        default=2, ge=1, le=30, description="Base delay between retries (seconds)"
    )
    flood_sleep_threshold: int = Field(
        default=60,
        ge=0,
        le=300,
        description="Auto-sleep threshold for FloodWait (seconds)",
    )
    connection_timeout: int = Field(
        default=30, ge=5, le=120, description="Connection timeout (seconds)"
    )

    # === Paths ===
    sessions_dir: str = Field(
        default="./sessions", description="Directory for session files"
    )
    storage_dir: str = Field(
        default="./storage", description="Directory for general storage (tdata, etc.)"
    )

    # === Per-account API settings ===
    account_json_filenames: str = Field(
        default="api.json,config.json,credentials.json,app.json",
        description="Comma-separated list of JSON filenames to search for api_id/api_hash",
    )
    fallback_env_api: bool = Field(
        default=True,
        description="Use TG_API_ID/TG_API_HASH from .env.example if account JSON not found",
    )

    # === Feature flags ===
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    @property
    def account_json_filenames_list(self) -> List[str]:
        """Список имён JSON файлов для поиска."""
        return [f.strip() for f in self.account_json_filenames.split(",") if f.strip()]

    # === Aliases для совместимости ===
    @property
    def api_id(self) -> int:
        """Alias для tg_api_id."""
        return self.tg_api_id

    @property
    def api_hash(self) -> str:
        """Alias для tg_api_hash."""
        return self.tg_api_hash

    @property
    def bot_token(self) -> str:
        """Alias для tg_bot_token."""
        return self.tg_bot_token

    @property
    def admin_ids_list(self) -> List[int]:
        """Парсинг admin_ids в список."""
        if not self.admin_ids:
            return []
        return [
            int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()
        ]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    def ensure_directories(self) -> None:
        """Создать необходимые директории."""
        Path(self.sessions_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

    def validate_telegram_config(self) -> tuple[bool, Optional[str]]:
        """
        Проверить наличие Telegram конфигурации.

        Returns:
            (is_valid, error_message)
        """
        if not self.tg_api_id:
            return False, "TG_API_ID не задан"
        if not self.tg_api_hash:
            return False, "TG_API_HASH не задан"
        if not self.tg_bot_token:
            return False, "TG_BOT_TOKEN не задан"
        return True, None


@lru_cache
def get_settings() -> Settings:
    """
    Получить настройки (кэшируется).

    Использование:
        from config import get_settings
        settings = get_settings()
    """
    return Settings()


# Для обратной совместимости
settings = get_settings()
