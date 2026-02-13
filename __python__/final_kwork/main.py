"""
Точка входа: запуск Telegram-бота.

Включает:
- Graceful shutdown
- Инициализацию БД
- Инициализацию пула прокси
- Регистрацию обработчиков
- Устойчивую обработку сетевых ошибок
- Совместимость с Telethon 2.0
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional


# Проверка зависимостей
def check_dependencies():
    """Проверка критических зависимостей."""
    import importlib.util

    missing = []

    if importlib.util.find_spec("python_socks") is None:
        missing.append("python-socks")  # type: ignore

    if importlib.util.find_spec("aiohttp") is None:
        missing.append("aiohttp")  # type: ignore

    if missing:
        print(f"❌ ОШИБКА: Не установлены зависимости: {', '.join(missing)}")  # type: ignore
        print(f"   Запустите: pip install {' '.join(missing)}")  # type: ignore
        print(f"   Или: .venv\\Scripts\\pip install {' '.join(missing)}")  # type: ignore
        sys.exit(1)


check_dependencies()

from dotenv import load_dotenv

# Загружаем .env.example до импорта config
load_dotenv()

# Используем адаптер для совместимости с Telethon 2.0
from services.telethon_adapter import (
    TelegramClient,
    start_bot_client,
    run_client_until_disconnected,
    TELETHON_VERSION,
)

from config import settings
from db.base import init_db
from bot.dispatcher import register_all_handlers
from utils.logging_config import setup_logging

# Глобальные переменные для graceful shutdown
_client: Optional[TelegramClient] = None
_shutdown_event: Optional[asyncio.Event] = None
logger: Optional[logging.Logger] = None

# Сетевые ошибки Windows
NETWORK_ERROR_CODES = {121, 1231, 1236}


def is_network_error(error: Exception) -> bool:
    """Проверить, является ли ошибка сетевой."""
    if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return True

    if isinstance(error, OSError):
        errno = getattr(error, "winerror", None) or getattr(error, "errno", None)
        if errno in NETWORK_ERROR_CODES:
            return True
        error_str = str(error).lower()
        if any(
            x in error_str for x in ["connection", "network", "timeout", "unreachable"]
        ):
            return True

    return False


def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """Настройка обработчиков сигналов для graceful shutdown."""

    def signal_handler(sig):
        logger.info(f"Получен сигнал {sig.name}, завершаю работу...")
        if _shutdown_event:
            _shutdown_event.set()

    # Для Windows используем другой подход
    if sys.platform == "win32":

        def win_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, завершаю работу...")
            if _shutdown_event:
                loop.call_soon_threadsafe(_shutdown_event.set)

        signal.signal(signal.SIGINT, win_handler)
        signal.signal(signal.SIGTERM, win_handler)
    else:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))


async def shutdown(client: TelegramClient) -> None:
    """Graceful shutdown процедура."""
    logger.info("Начинаю graceful shutdown...")

    # Останавливаем ProxyPool
    try:
        from services.proxy_pool import get_proxy_pool, sync_proxy_status_to_db

        pool = get_proxy_pool()
        await pool.stop_background_checker()
        await sync_proxy_status_to_db()
        logger.info("ProxyPool остановлен")
    except Exception as e:
        logger.warning(f"Ошибка при остановке ProxyPool: {e}")

    # Останавливаем всех workers
    try:
        from services.telethon_workers import stop_all_workers

        stopped = await stop_all_workers()
        if stopped:
            logger.info(f"Остановлено {stopped} воркеров")
    except Exception as e:
        logger.warning(f"Ошибка при остановке воркеров: {e}")

    # Отключаем клиента
    if client and client.is_connected():
        try:
            await client.disconnect()
            logger.info("Telegram клиент отключён")
        except Exception as e:
            logger.warning(f"Ошибка при отключении клиента: {e}")

    logger.info("Graceful shutdown завершён")


async def main() -> None:
    """Главная функция запуска."""
    global _client, _shutdown_event, logger

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Telethon version: {TELETHON_VERSION}")

    # Проверка конфигурации
    if not settings.api_id or not settings.api_hash or not settings.bot_token:
        logger.error("Не заданы TG_API_ID, TG_API_HASH или TG_BOT_TOKEN")
        return

    if not settings.admin_ids:
        logger.warning("ADMIN_IDS не задан — команды админа не будут работать")

    # Создание папки для сессий
    os.makedirs(settings.sessions_dir, exist_ok=True)

    # Инициализация БД
    logger.info("Инициализация базы данных...")
    await init_db()

    # Инициализация ProxyPool
    logger.info("Инициализация ProxyPool...")
    try:
        from services.proxy_pool import get_proxy_pool, load_proxies_from_db

        proxy_count = await load_proxies_from_db()
        if proxy_count > 0:
            pool = get_proxy_pool()
            await pool.start_background_checker(interval=300)  # Проверка каждые 5 мин
            logger.info(f"ProxyPool запущен с {proxy_count} прокси")
        else:
            logger.info("Прокси не найдены, работаем на main IP")
    except Exception as e:
        logger.warning(f"Ошибка инициализации ProxyPool: {e}")

    # Создание клиента бота с параметрами устойчивости
    _client = TelegramClient(
        "test_bot_session",
        # "bot_session.session",
        settings.api_id,
        settings.api_hash,
        device_model="Windows 10 x64",
        system_version="Windows 10",
        app_version="4.16.8 x64",
        lang_code="en",
        system_lang_code="en-us",
        connection_retries=settings.connection_retries,
        retry_delay=settings.retry_delay,
        auto_reconnect=True,
        timeout=settings.connection_timeout,
    )

    # Событие для shutdown
    _shutdown_event = asyncio.Event()

    # Настройка сигналов
    loop = asyncio.get_running_loop()
    setup_signal_handlers(loop)

    # Регистрация обработчиков
    register_all_handlers(_client)

    # Основной цикл с автоматическим переподключением
    reconnect_count = 0
    max_reconnects = 10
    reconnect_delay = 5

    while reconnect_count < max_reconnects:
        try:
            # Запуск бота (совместимо с v1 и v2)
            logger.info("Запуск бота...")
            await start_bot_client(_client, settings.bot_token)

            me = await _client.get_me()
            logger.info(f"Бот запущен: @{me.username}")

            # Сбрасываем счётчик при успешном подключении
            reconnect_count = 0

            # Ждём сигнала завершения или отключения
            async def wait_disconnect():
                try:
                    await run_client_until_disconnected(_client)
                except (ConnectionError, TimeoutError, OSError) as e:
                    if is_network_error(e):
                        logger.warning(f"Сетевая ошибка в wait_disconnect: {e}")
                        raise
                    raise

            disconnect_task = asyncio.create_task(wait_disconnect())
            shutdown_task = asyncio.create_task(_shutdown_event.wait())

            done, pending = await asyncio.wait(
                [disconnect_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Проверяем, была ли это ошибка сети
            for task in done:
                try:
                    exc = task.exception()
                    if exc and is_network_error(exc):
                        raise exc
                except asyncio.CancelledError:
                    pass
                except asyncio.InvalidStateError:
                    pass

            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Если shutdown event - выходим из цикла
            if _shutdown_event.is_set():
                break

        except (ConnectionError, TimeoutError, asyncio.TimeoutError, OSError) as e:
            if is_network_error(e):
                reconnect_count += 1
                delay = min(reconnect_delay * reconnect_count, 60)  # Max 60 сек
                logger.warning(
                    f"Сетевая ошибка, переподключение через {delay}с (попытка {reconnect_count}/{max_reconnects}): {e}"
                )

                # Отключаем клиента
                if _client and _client.is_connected():
                    try:
                        await _client.disconnect()
                    except Exception:
                        pass

                await asyncio.sleep(delay)
                continue
            else:
                logger.exception(f"Критическая ошибка: {e}")
                break

        except Exception as e:
            logger.exception(f"Критическая ошибка: {e}")
            break

    if reconnect_count >= max_reconnects:
        logger.error(
            f"Превышено максимальное количество переподключений ({max_reconnects})"
        )

    await shutdown(_client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
