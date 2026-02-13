"""
Диспетчер: регистрация всех обработчиков.
"""
from services.telethon_adapter import TelegramClient

from bot.handlers_manager import register_manager_handlers
from bot.handlers_admin import register_admin_handlers


def register_all_handlers(client: TelegramClient) -> None:
    """Регистрация всех обработчиков бота."""
    register_manager_handlers(client)
    register_admin_handlers(client)
