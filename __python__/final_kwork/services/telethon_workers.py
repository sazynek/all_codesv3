"""
Менеджер Telethon-воркеров для перехвата кодов подтверждения.

Включает:
- Корректную обработку ошибок Telethon
- Graceful retry при сетевых ошибках
- Автоматическую смену прокси при неудачах
- Backoff-алгоритм для повторных попыток
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Optional

from services.telethon_adapter import TelegramClient, events
from telethon.tl.functions.auth import ResetAuthorizationsRequest
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    SessionPasswordNeededError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    RPCError,
)

from config import settings

logger = logging.getLogger(__name__)

# Типы callbacks
CodeCallback = Callable[[int, int, str], Awaitable[None]]
TimeoutCallback = Callable[[int, int], Awaitable[None]]
ErrorCallback = Callable[[int, int, str], Awaitable[None]]
# on_connected(account_id, manager_tg_id, phone, username, is_premium)
ConnectedCallback = Callable[[int, int, Optional[str], Optional[str], bool], Awaitable[None]]

# Активные воркеры: account_id -> task
_active_workers: Dict[int, asyncio.Task] = {}

# Regex для поиска кода (5-6 цифр)
CODE_PATTERN = re.compile(r"\b(\d{5,6})\b")

# Константы retry
MAX_CONNECTION_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # секунды между попытками

# Сетевые ошибки Windows (WinError)
NETWORK_ERROR_CODES = {
    121,   # ERROR_SEM_TIMEOUT - Semaphore timeout
    1231,  # ERROR_NETWORK_UNREACHABLE - Network unreachable
    1236,  # ERROR_CONNECTION_ABORTED - Connection aborted
}


def is_network_error(error: Exception) -> bool:
    """Проверить, является ли ошибка сетевой."""
    if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return True
    
    if isinstance(error, OSError):
        # Проверяем WinError коды
        errno = getattr(error, 'winerror', None) or getattr(error, 'errno', None)
        if errno in NETWORK_ERROR_CODES:
            return True
        # Также проверяем текст ошибки
        error_str = str(error).lower()
        if any(x in error_str for x in ['connection', 'network', 'timeout', 'unreachable']):
            return True
    
    return False


@dataclass
class WorkerStatus:
    """Статус воркера."""
    account_id: int
    is_running: bool
    error: Optional[str] = None


def get_active_workers_count() -> int:
    """Количество активных воркеров."""
    return len(_active_workers)


def get_active_worker_ids() -> list[int]:
    """ID аккаунтов с активными воркерами."""
    return list(_active_workers.keys())


async def stop_code_listener(account_id: int) -> bool:
    """
    Остановить слушатель для аккаунта.

    Returns:
        True если воркер был остановлен, False если не найден.
    """
    task = _active_workers.pop(account_id, None)
    if not task:
        return False

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        # Важно: не пробрасываем ошибки воркера наружу (иначе могут откатиться транзакции revoke/approve)
        logger.warning(f"[worker] stop_code_listener got exception for account_id={account_id}: {e}")

    logger.info(f"[worker] stopped for account_id={account_id}")
    return True





def _proxy_dict_to_telethon(proxy: dict):
    """Конвертировать прокси-словарь в формат Telethon."""
    if not proxy:
        return None
    proxy_type_map = {
        'socks5': 2,
        'socks4': 1,
        'http': 3,
        'https': 3,
    }
    ptype = proxy_type_map.get(str(proxy.get('proxy_type', 'http')).lower(), 3)
    return (
        ptype,
        proxy.get('addr'),
        int(proxy.get('port')),
        True,  # rdns
        proxy.get('username'),
        proxy.get('password'),
    )


async def reset_other_sessions(
    account_id: int,
    session_path: str,
    account_phone: str | None = None,
    proxy: dict | None = None,
    api_id: int | None = None,
    api_hash: str | None = None,
    device_model: str | None = None,
    system_version: str | None = None,
    app_version: str | None = None,
    lang_code: str | None = None,
    system_lang_code: str | None = None,
    timeout_sec: int = 25,
) -> bool:
    """Сбросить ВСЕ другие авторизации (сессии) аккаунта.

    Telegram не выкидывает текущую сессию, с которой выполняется запрос.
    Значит бот останется авторизован, а все остальные устройства (в т.ч. менеджер)
    будут разлогинены.

    Возвращает True при успехе. Ошибки наружу не пробрасывает.
    """
    import os

    if not session_path:
        logger.warning(f"[reset_auth] no session_path for account_id={account_id}")
        return False

    session_name = session_path.replace('.session', '')
    if not os.path.exists(session_path) and not os.path.exists(f"{session_name}.session"):
        logger.warning(f"[reset_auth] session file not found for account_id={account_id}: {session_path}")
        return False

    use_api_id = api_id or settings.api_id
    use_api_hash = api_hash or settings.api_hash

    # Подберём прокси из пула, если не передали
    use_proxy = proxy
    if use_proxy is None:
        try:
            from services.proxy_pool import get_proxy_pool
            from services.proxy_service import get_country_by_phone

            account_country = get_country_by_phone(account_phone) if account_phone else None
            pool = get_proxy_pool()
            proxy_info = await pool.get_proxy_for_account(account_id, account_country)
            if proxy_info:
                use_proxy = proxy_info.to_dict()
        except Exception as e:
            logger.debug(f"[reset_auth] proxy selection failed for account_id={account_id}: {e}")

    telethon_proxy = _proxy_dict_to_telethon(use_proxy) if use_proxy else None

    # Fingerprint
    use_device_model = device_model or "Samsung SM-S918B"
    use_system_version = system_version or "SDK 34"
    use_app_version = app_version or "10.14.5 (5447)"
    use_lang_code = lang_code or "en"
    use_system_lang_code = system_lang_code or "en"

    client = None
    try:
        client = TelegramClient(
            session_name,
            use_api_id,
            use_api_hash,
            proxy=telethon_proxy,
            device_model=use_device_model,
            system_version=use_system_version,
            app_version=use_app_version,
            lang_code=use_lang_code,
            system_lang_code=use_system_lang_code,
        )

        async def _do() -> bool:
            await client.connect()
            if not await client.is_user_authorized():
                logger.warning(f"[reset_auth] not authorized for account_id={account_id}")
                return False
            await client(ResetAuthorizationsRequest())
            return True

        ok = await asyncio.wait_for(_do(), timeout=timeout_sec)
        logger.info(f"[reset_auth] ResetAuthorizations done for account_id={account_id}")
        return bool(ok)

    except FloodWaitError as e:
        logger.warning(f"[reset_auth] FloodWait for account_id={account_id}: {getattr(e, 'seconds', '?')}s")
        return False
    except Exception as e:
        logger.warning(f"[reset_auth] failed for account_id={account_id}: {e}")
        return False
    finally:
        if client is not None:
            try:
                await client.disconnect()
            except Exception:
                pass


async def stop_all_workers() -> int:
    """
    Остановить все воркеры.
    
    Returns:
        Количество остановленных воркеров.
    """
    count = len(_active_workers)
    
    for account_id in list(_active_workers.keys()):
        await stop_code_listener(account_id)
    
    logger.info(f"[worker] stopped all {count} workers")
    return count


async def start_code_listener(
    account_id: int,
    session_path: str,
    manager_tg_id: int,
    on_code_received: CodeCallback,
    on_timeout: TimeoutCallback,
    on_error: ErrorCallback,
    bot_client: TelegramClient,
    proxy: Optional[dict] = None,
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    account_phone: Optional[str] = None,
    # Device fingerprint
    device_model: Optional[str] = None,
    system_version: Optional[str] = None,
    app_version: Optional[str] = None,
    lang_code: Optional[str] = None,
    system_lang_code: Optional[str] = None,
    # Callback при успешном подключении (для отправки номера)
    on_connected: Optional[ConnectedCallback] = None,
) -> bool:
    """
    Запустить слушатель для перехвата кода подтверждения.
    
    Включает:
    - Retry при сетевых ошибках с backoff
    - Автоматическую смену прокси при неудачах
    - Graceful shutdown
    - Device fingerprint для стабильности сессии
    
    Args:
        account_id: ID аккаунта в БД
        session_path: Путь к session-файлу
        manager_tg_id: Telegram ID менеджера
        on_code_received: Callback при получении кода
        on_timeout: Callback при таймауте
        on_error: Callback при ошибке
        bot_client: Клиент бота для отправки сообщений
        proxy: Словарь с параметрами прокси (опционально)
               Формат: {'proxy_type': 'socks5', 'addr': 'host', 'port': 1080, 'username': None, 'password': None}
        api_id: API ID аккаунта (если None - из настроек)
        api_hash: API Hash аккаунта (если None - из настроек)
        account_phone: Номер телефона аккаунта (для определения страны при смене прокси)
        device_model: Device model для fingerprint
        system_version: System version для fingerprint
        app_version: App version для fingerprint
        lang_code: Language code
        system_lang_code: System language code
    
    Returns:
        True если воркер запущен успешно.
    """
    import os
    
    # Используем переданные credentials или из настроек
    use_api_id = api_id or settings.api_id
    use_api_hash = api_hash or settings.api_hash
    
    # Device fingerprint - актуальные дефолтные значения Android если не переданы
    use_device_model = device_model or "Samsung SM-S918B"
    use_system_version = system_version or "SDK 34"
    use_app_version = app_version or "10.14.5 (5447)"
    use_lang_code = lang_code or "en"
    use_system_lang_code = system_lang_code or "en"
    
    logger.info(
        f"[worker] fingerprint for account_id={account_id}: "
        f"device='{use_device_model}', system='{use_system_version}', "
        f"app='{use_app_version}', lang={use_lang_code}/{use_system_lang_code}"
    )
    
    # Определяем страну аккаунта по номеру телефона
    account_country = None
    if account_phone:
        from services.proxy_service import get_country_by_phone
        account_country = get_country_by_phone(account_phone)
        if account_country:
            logger.info(f"[worker] account {account_id} country: {account_country} (phone: {account_phone})")
    
    # Проверяем путь к сессии
    if not session_path:
        logger.error(f"[worker] no session_path for account_id={account_id}")
        await on_error(account_id, manager_tg_id, "Путь к сессии не указан")
        return False
    
    # Убираем .session если есть (Telethon добавит сам)
    session_name = session_path.replace('.session', '')
    
    if not os.path.exists(session_path) and not os.path.exists(f"{session_name}.session"):
        logger.error(f"[worker] session file not found: {session_path}")
        await on_error(account_id, manager_tg_id, "Файл сессии не найден")
        return False
    
    # Отменяем предыдущий воркер если есть
    if account_id in _active_workers:
        await stop_code_listener(account_id)
    
    async def worker():
        client: Optional[TelegramClient] = None
        code_found = asyncio.Event()
        found_code: Optional[str] = None
        current_proxy = proxy
        retry_count = 0
        
        async def try_connect() -> Optional[TelegramClient]:
            """Попытка подключения с текущим прокси."""
            nonlocal current_proxy, retry_count
            
            # Формируем параметры прокси для Telethon
            telethon_proxy = None
            if current_proxy:
                proxy_type_map = {
                    'socks5': 2,
                    'socks4': 1,
                    'http': 3,
                    'https': 3,
                }
                ptype = proxy_type_map.get(current_proxy.get('proxy_type', 'http'), 3)
                telethon_proxy = (
                    ptype,
                    current_proxy['addr'],
                    current_proxy['port'],
                    True,
                    current_proxy.get('username'),
                    current_proxy.get('password'),
                )
                # Маскируем credentials в логах
                masked_addr = f"{current_proxy['addr']}:{current_proxy['port']}"
                logger.info(f"[worker] using proxy: {current_proxy.get('proxy_type', 'http')}://{masked_addr}")
            else:
                logger.info(f"[worker] using direct connection (no proxy)")
            
            new_client = TelegramClient(
                session_name,
                use_api_id,
                use_api_hash,
                device_model=use_device_model,
                system_version=use_system_version,
                app_version=use_app_version,
                lang_code=use_lang_code,
                system_lang_code=use_system_lang_code,
                connection_retries=settings.connection_retries,
                retry_delay=settings.retry_delay,
                timeout=settings.connection_timeout,
                proxy=telethon_proxy,
            )
            
            await new_client.connect()
            return new_client
        
        async def get_new_proxy() -> Optional[dict]:
            """Получить новый прокси из пула с учётом страны аккаунта."""
            try:
                from services.proxy_pool import get_proxy_pool
                pool = get_proxy_pool()
                
                # Помечаем текущий как неудачный
                if current_proxy:
                    from services.proxy_pool import ProxyInfo
                    proxy_info = ProxyInfo(
                        proxy_type=current_proxy.get('proxy_type', 'http'),
                        host=current_proxy['addr'],
                        port=current_proxy['port'],
                        username=current_proxy.get('username'),
                        password=current_proxy.get('password'),
                    )
                    await pool.mark_proxy_failed(proxy_info)
                
                # Получаем новый с учётом страны аккаунта
                new_proxy = await pool.get_new_proxy_for_account(account_id, account_country=account_country)
                if new_proxy:
                    return new_proxy.to_dict()
            except Exception as e:
                logger.warning(f"[worker] failed to get new proxy: {e}")
            
            return None
        
        try:
            logger.info(f"[worker] starting for account_id={account_id}")
            
            # Цикл подключения с retry
            while retry_count < MAX_CONNECTION_RETRIES:
                try:
                    client = await try_connect()
                    break  # Успешное подключение
                    
                except (ConnectionError, TimeoutError, asyncio.TimeoutError, OSError) as e:
                    retry_count += 1
                    
                    if not is_network_error(e):
                        # Не сетевая ошибка - выходим
                        logger.error(f"[worker] connection error for account_id={account_id}: {e}")
                        await on_error(account_id, manager_tg_id, f"Ошибка подключения: {e}")
                        return
                    
                    logger.warning(f"[worker] network error for account_id={account_id} (attempt {retry_count}/{MAX_CONNECTION_RETRIES}): {e}")
                    
                    if retry_count >= MAX_CONNECTION_RETRIES:
                        logger.error(f"[worker] max retries exceeded for account_id={account_id}")
                        await on_error(account_id, manager_tg_id, f"Не удалось подключиться после {retry_count} попыток")
                        return
                    
                    # Пробуем сменить прокси
                    new_proxy = await get_new_proxy()
                    if new_proxy:
                        current_proxy = new_proxy
                        logger.info(f"[worker] switched to new proxy for account_id={account_id}")
                    
                    # Backoff
                    delay = RETRY_DELAYS[min(retry_count - 1, len(RETRY_DELAYS) - 1)]
                    logger.info(f"[worker] waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
            
            if client is None:
                await on_error(account_id, manager_tg_id, "Не удалось создать подключение")
                return
            
            logger.info(f"[worker] connected, using api_id={use_api_id} for account_id={account_id}")
            
            # Регистрируем handler для сообщений
            @client.on(events.NewMessage(incoming=True))
            async def message_handler(event):
                nonlocal found_code
                text = event.message.message or ""
                sender_id = event.sender_id
                
                logger.debug(f"[worker] incoming message for account_id={account_id}: sender_id={sender_id}")
                
                # Ищем код в сообщении
                match = CODE_PATTERN.search(text)
                if match:
                    found_code = match.group(1)
                    logger.info(f"[worker] code found for account_id={account_id}: {found_code}")
                    code_found.set()
            
            async def mark_account_disabled(error_text: str):
                """Пометить аккаунт как отключённый."""
                try:
                    from db.session import get_session
                    from db.models import Account, AccountStatus
                    from sqlalchemy import select
                    
                    async with get_session() as db_session:
                        stmt = select(Account).where(Account.id == account_id)
                        result = await db_session.execute(stmt)
                        account = result.scalar_one_or_none()
                        if account:
                            account.status = AccountStatus.DISABLED
                            account.error_text = error_text
                            await db_session.commit()
                            logger.info(f"[worker] marked account {account_id} as DISABLED: {error_text}")
                except Exception as e:
                    logger.warning(f"[worker] failed to mark account as disabled: {e}")
            
            # Проверяем авторизацию
            try:
                if not await client.is_user_authorized():
                    logger.error(f"[worker] not authorized: account_id={account_id}")
                    await mark_account_disabled("Сессия не авторизована (мёртвая)")
                    await on_error(account_id, manager_tg_id, "❌ Сессия мёртвая — аккаунт был отозван или удалён")
                    return
            except AuthKeyUnregisteredError:
                logger.error(f"[worker] auth key unregistered: account_id={account_id}")
                await mark_account_disabled("Auth key unregistered")
                await on_error(account_id, manager_tg_id, "❌ Сессия отозвана Telegram'ом")
                return
            except SessionPasswordNeededError:
                logger.error(f"[worker] 2FA required: account_id={account_id}")
                await on_error(account_id, manager_tg_id, "⚠️ Требуется пароль 2FA — обратитесь к администратору")
                return
            except (UserDeactivatedError, UserDeactivatedBanError):
                logger.error(f"[worker] user deactivated: account_id={account_id}")
                await mark_account_disabled("Аккаунт забанен/удалён")
                await on_error(account_id, manager_tg_id, "❌ Аккаунт забанен или удалён Telegram'ом")
                return
            
            # Получаем информацию о пользователе и обновляем tg_user_id если нужно
            real_phone = None
            real_username = None
            is_premium = False
            try:
                me = await client.get_me()
                if me:
                    real_user_id = me.id
                    real_phone = me.phone
                    real_username = me.username
                    is_premium = getattr(me, 'premium', False) or False
                    
                    # Обновляем аккаунт в БД если tg_user_id был None или phone не заполнен
                    from db.session import get_session
                    from db.models import Account
                    from sqlalchemy import select
                    
                    async with get_session() as db_session:
                        stmt = select(Account).where(Account.id == account_id)
                        result = await db_session.execute(stmt)
                        account = result.scalar_one_or_none()
                        
                        need_update = False
                        need_move_session = False
                        
                        if account and not account.tg_user_id:
                            # Проверяем дубликат
                            dup_stmt = select(Account).where(
                                Account.tg_user_id == real_user_id,
                                Account.id != account_id
                            )
                            dup_result = await db_session.execute(dup_stmt)
                            duplicate = dup_result.scalar_one_or_none()
                            
                            if duplicate:
                                logger.warning(f"[worker] found duplicate tg_user_id={real_user_id}, account #{duplicate.id}")
                                await on_error(
                                    account_id, manager_tg_id, 
                                    f"Дубликат! Аккаунт уже существует: #{duplicate.id}"
                                )
                                return
                            
                            # Обновляем данные
                            account.tg_user_id = real_user_id
                            need_update = True
                            need_move_session = True  # Нужно перенести сессию
                        
                        # Обновляем phone если не было
                        if account and not account.phone and real_phone:
                            account.phone = real_phone
                            need_update = True
                        
                        # Обновляем username если не было
                        if account and real_username and not account.username:
                            account.username = real_username
                            need_update = True
                        
                        # Обновляем is_premium
                        if account and account.is_premium != is_premium:
                            account.is_premium = is_premium
                            need_update = True
                            
                        if need_update and account:
                            # Переносим сессию в правильную папку если нужно
                            if need_move_session:
                                import shutil
                                old_path = account.session_path
                                new_dir = f"./storage/sessions/{real_user_id}"
                                new_path = f"{new_dir}/account.session"
                                
                                if old_path and old_path != new_path:
                                    import os
                                    os.makedirs(new_dir, exist_ok=True)
                                    if os.path.exists(old_path):
                                        shutil.copy2(old_path, new_path)
                                        account.session_path = new_path
                                        # Удаляем старую папку pending_*
                                        old_dir = os.path.dirname(old_path)
                                        if "pending_" in old_dir:
                                            shutil.rmtree(old_dir, ignore_errors=True)
                            
                            await db_session.commit()
                            logger.info(f"[worker] updated account {account_id}: tg_user_id={real_user_id}, phone={real_phone}")
                        
                        elif account and account.tg_user_id and account.tg_user_id != real_user_id:
                            logger.warning(
                                f"[worker] tg_user_id mismatch! DB={account.tg_user_id}, real={real_user_id}"
                            )
                    
                    # Вызываем callback on_connected с данными пользователя
                    if on_connected:
                        try:
                            await on_connected(account_id, manager_tg_id, real_phone, real_username, is_premium)
                        except Exception as e:
                            logger.warning(f"[worker] on_connected callback failed: {e}")
                            
            except Exception as e:
                logger.warning(f"[worker] failed to get/update user info: {e}")
            
            # Уведомляем менеджера
            try:
                await bot_client.send_message(
                    manager_tg_id,
                    f"⏳ Ожидаю код подтверждения...\n"
                    f"Таймаут: {settings.code_wait_timeout} сек.\n\n"
                    f"💡 Если код придёт по SMS, сообщите администратору."
                )
            except Exception as e:
                logger.warning(f"[worker] failed to notify manager: {e}")
            
            # Ждём коды с таймаутом. В отличие от «одного кода», тут можем поймать
            # несколько кодов подряд (если менеджер повторно инициирует вход).
            # Это убирает необходимость «отзывать и выдавать заново».
            loop = asyncio.get_running_loop()
            deadline = loop.time() + settings.code_wait_timeout
            last_sent: Optional[str] = None

            try:
                while True:
                    remaining = deadline - loop.time()
                    if remaining <= 0:
                        raise asyncio.TimeoutError

                    await asyncio.wait_for(code_found.wait(), timeout=remaining)

                    code_found.clear()
                    code = found_code
                    found_code = None

                    if not code:
                        continue

                    # Не спамим одинаковым кодом
                    if code == last_sent:
                        continue
                    last_sent = code

                    # Помечаем прокси как успешный
                    if current_proxy:
                        try:
                            from services.proxy_pool import get_proxy_pool, ProxyInfo
                            pool = get_proxy_pool()
                            proxy_info = ProxyInfo(
                                proxy_type=current_proxy.get('proxy_type', 'http'),
                                host=current_proxy['addr'],
                                port=current_proxy['port'],
                                username=current_proxy.get('username'),
                                password=current_proxy.get('password'),
                            )
                            await pool.mark_proxy_success(proxy_info)
                        except Exception:
                            pass

                    await on_code_received(account_id, manager_tg_id, code)

            except asyncio.TimeoutError:
                logger.warning(f"[worker] timeout for account_id={account_id}")
                await on_timeout(account_id, manager_tg_id)
        
        except asyncio.CancelledError:
            logger.info(f"[worker] cancelled for account_id={account_id}")
            raise
        
        except FloodWaitError as e:
            wait_time = getattr(e, 'seconds', 30)
            logger.error(f"[worker] flood wait {wait_time}s for account_id={account_id}")
            await on_error(
                account_id, manager_tg_id, 
                f"Telegram ограничил запросы. Подождите {wait_time} секунд."
            )
        
        except RPCError as e:
            logger.error(f"[worker] RPC error for account_id={account_id}: {e}")
            await on_error(account_id, manager_tg_id, f"Ошибка Telegram API: {getattr(e, 'message', str(e))}")
        
        except Exception as e:
            # Обрабатываем сетевые ошибки во время работы
            if is_network_error(e):
                logger.warning(f"[worker] network error during operation for account_id={account_id}: {e}")
                await on_error(account_id, manager_tg_id, f"Сетевая ошибка: {e}")
            else:
                logger.exception(f"[worker] unexpected error for account_id={account_id}")
                await on_error(account_id, manager_tg_id, f"Неожиданная ошибка: {e}")
        
        finally:
            # Гарантированно закрываем клиент
            if client is not None:
                try:
                    await client.disconnect()
                except Exception as e:
                    logger.debug(f"[worker] disconnect error (ignored): {e}")
            
            _active_workers.pop(account_id, None)
            logger.info(f"[worker] finished for account_id={account_id}")
    
    # Создаём задачу с обработкой исключений
    async def safe_worker():
        """Обёртка для перехвата необработанных исключений."""
        try:
            await worker()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"[worker] unhandled error for account_id={account_id}: {e}")
            try:
                await on_error(account_id, manager_tg_id, f"Критическая ошибка: {e}")
            except Exception:
                pass
    
    task = asyncio.create_task(safe_worker())
    
    # Добавляем callback для логирования необработанных исключений
    def task_done_callback(t: asyncio.Task):
        try:
            exc = t.exception()
            if exc and not isinstance(exc, asyncio.CancelledError):
                logger.error(f"[worker] task exception for account_id={account_id}: {exc}")
        except asyncio.CancelledError:
            pass
        except asyncio.InvalidStateError:
            pass
    
    task.add_done_callback(task_done_callback)
    _active_workers[account_id] = task
    
    return True
