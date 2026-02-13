"""
Адаптер для совместимости с Telethon 1.x и 2.0.

Обеспечивает единый интерфейс для работы с Telethon,
скрывая различия между версиями.
"""
import asyncio
import logging
from typing import Any, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

# Определяем версию Telethon
try:
    from telethon import version
    TELETHON_VERSION = version.__version__
    IS_V2 = TELETHON_VERSION.startswith('2.')
except (ImportError, AttributeError):
    TELETHON_VERSION = "unknown"
    IS_V2 = False

logger.info(f"Telethon version: {TELETHON_VERSION}, is_v2: {IS_V2}")

# === Импорты в зависимости от версии ===

if IS_V2:
    # Telethon 2.0
    try:
        from telethon import Client
        from telethon import events
        from telethon.types import Button
        from telethon.errors import (
            AuthKeyUnregisteredError,
            SessionPasswordNeededError,
            FloodWaitError,
            RPCError,
        )
        TelegramClient = Client
    except ImportError as e:
        logger.error(f"Telethon 2.0 import failed: {e}. Falling back to v1 imports.")
        IS_V2 = False
        from telethon import TelegramClient, events, Button
        from telethon.errors import (
            AuthKeyUnregisteredError,
            SessionPasswordNeededError,
            FloodWaitError,
            RPCError,
        )
        Client = TelegramClient
else:
    # Telethon 1.x
    from telethon import TelegramClient, events, Button
    from telethon.errors import (
        AuthKeyUnregisteredError,
        SessionPasswordNeededError,
        FloodWaitError,
        RPCError,
    )
    Client = TelegramClient


async def start_bot_client(client: Any, bot_token: str) -> None:
    """
    Запустить клиента бота (совместимо с v1 и v2).
    
    В Telethon 1.x: client.start(bot_token=...)
    В Telethon 2.0: client.connect() + sign_in
    """
    if IS_V2:
        await client.connect()
        if not await client.is_user_authorized():
            await client.sign_in(bot_token=bot_token)
    else:
        await client.start(bot_token=bot_token)


async def start_user_client(client: Any) -> bool:
    """
    Запустить клиента пользователя (только connect).
    
    Returns:
        True если авторизован, False если нет.
    """
    await client.connect()
    return await client.is_user_authorized()


async def run_client_until_disconnected(client: Any) -> None:
    """Запустить клиента до отключения (совместимо с v1 и v2)."""
    if IS_V2:
        try:
            await client.run_until_disconnected()
        except AttributeError:
            while client.is_connected():
                await asyncio.sleep(1)
    else:
        await client.run_until_disconnected()


def get_flood_wait_seconds(error: Any) -> int:
    """Получить время ожидания из FloodWaitError (совместимо с v1 и v2)."""
    if IS_V2:
        return getattr(error, 'value', getattr(error, 'seconds', 30))
    return getattr(error, 'seconds', 30)


def get_user_premium(user: Any) -> Optional[bool]:
    """Получить статус Premium пользователя (совместимо с v1 и v2)."""
    for attr in ['premium', 'is_premium', '_premium']:
        if hasattr(user, attr):
            return getattr(user, attr)
    return None


# Реэкспортируем события для удобства
NewMessage = events.NewMessage
CallbackQuery = events.CallbackQuery

__all__ = [
    'TelegramClient',
    'Client', 
    'events',
    'Button',
    'NewMessage',
    'CallbackQuery',
    'AuthKeyUnregisteredError',
    'SessionPasswordNeededError',
    'FloodWaitError',
    'RPCError',
    'get_flood_wait_seconds',
    'start_bot_client',
    'start_user_client',
    'run_client_until_disconnected',
    'get_user_premium',
    'IS_V2',
    'TELETHON_VERSION',
]
