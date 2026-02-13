"""
Константы для бота.
"""
from typing import Final

# Ограничения файлов
MAX_FILE_SIZE: Final[int] = 100 * 1024 * 1024  # 100 MB

# Эмодзи для статусов аккаунтов
ACCOUNT_STATUS_EMOJI: Final[dict] = {
    "free": "🟢",
    "reserved": "🟡",
    "assigned": "🔵",
    "disabled": "🔴",
    "needs_conversion": "🟡",
}

# Названия статусов на русском
ACCOUNT_STATUS_NAMES: Final[dict] = {
    "free": "Свободен",
    "reserved": "Зарезервирован",
    "assigned": "Выдан",
    "disabled": "Невалид",
    "needs_conversion": "Требует конвертации",
}

# Алиас для обратной совместимости
STATUS_EMOJI_MAP = ACCOUNT_STATUS_EMOJI

# Эмодзи для статусов заявок
ISSUE_STATUS_EMOJI: Final[dict] = {
    "pending": "⏳",
    "code_wait": "🕒",
    "approved": "✅",
    "rejected": "❌",
    "revoked": "🔴",
    "timeout": "⏰",
}

# Названия статусов заявок на русском
ISSUE_STATUS_NAMES: Final[dict] = {
    "pending": "Ожидает",
    "code_wait": "Ожидаем код",
    "approved": "Активна",
    "rejected": "Отклонена",
    "revoked": "Отозвана",
    "timeout": "Таймаут",
}

# Callback data prefixes
CB_APPROVE: Final[str] = "approve:"
CB_REJECT: Final[str] = "reject:"
CB_REVOKE: Final[str] = "revoke:"
CB_CONFIRM: Final[str] = "confirm:"
CB_CANCEL: Final[str] = "cancel:"
CB_MENU_ADMIN: Final[str] = "menu_admin"
CB_MENU_MANAGER: Final[str] = "menu_manager"
CB_BACK: Final[str] = "back"

