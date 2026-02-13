"""
ProxyPool - устойчивый пул прокси с автоматическим восстановлением.

Особенности:
- Sticky-привязка: аккаунт держится на одном прокси пока живое
- Автоматическая смена прокси при сетевых ошибках
- Асинхронный чекер с таймаутом
- Статистика здоровых/мертвых прокси
- Fallback на main IP если прокси нет
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyStatus(Enum):
    """Статус прокси."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    CHECKING = "checking"


@dataclass
class ProxyInfo:
    """Информация о прокси."""

    proxy_type: str  # socks5, http, https
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

    # Лимит аккаунтов (0 = без лимита)
    max_accounts: int = 6

    # Страна прокси (ISO 3166-1 alpha-2)
    country: Optional[str] = None

    # Статус
    status: ProxyStatus = ProxyStatus.UNKNOWN
    last_check_time: Optional[float] = None
    last_check_ip: Optional[str] = None
    latency_ms: Optional[int] = None

    # Счетчики
    success_count: int = 0
    fail_count: int = 0
    consecutive_fails: int = 0

    # DB ID (если есть)
    db_id: Optional[int] = None

    def __hash__(self):
        return hash((self.host, self.port, self.proxy_type, self.username))

    def __eq__(self, other):
        if not isinstance(other, ProxyInfo):
            return False
        return (
            self.host == other.host
            and self.port == other.port
            and self.proxy_type == other.proxy_type
            and self.username == other.username
        )

    @property
    def is_healthy(self) -> bool:
        return self.status == ProxyStatus.HEALTHY

    @property
    def address(self) -> str:
        """Маскированный адрес для логов."""
        return f"{self.host}:{self.port}"

    @property
    def masked_credentials(self) -> str:
        """Маскированные credentials для логов."""
        if self.username:
            return f"{self.username[:3]}***@{self.address}"
        return self.address

    def to_telethon_format(self) -> Optional[tuple]:
        """
        Конвертировать в формат Telethon.

        Returns:
            (proxy_type, addr, port, rdns, username, password) или None
        """
        proxy_type_map = {
            "socks5": 2,
            "socks4": 1,
            "http": 3,
            "https": 3,
        }
        ptype = proxy_type_map.get(self.proxy_type.lower(), 3)
        return (
            ptype,
            self.host,
            self.port,
            True,  # rdns
            self.username,
            self.password,
        )

    def to_dict(self) -> dict:
        """Конвертировать в словарь для telethon_workers."""
        return {
            "proxy_type": self.proxy_type.lower(),
            "addr": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }


@dataclass
class ProxyPoolStats:
    """Статистика пула прокси."""

    total: int = 0
    healthy: int = 0
    unhealthy: int = 0
    unknown: int = 0
    checking: int = 0
    last_check_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "healthy": self.healthy,
            "unhealthy": self.unhealthy,
            "unknown": self.unknown,
            "checking": self.checking,
            "last_check_time": (
                self.last_check_time.isoformat() if self.last_check_time else None
            ),
        }


class ProxyPool:
    """
    Пул прокси с автоматическим управлением.

    Использование:
        pool = ProxyPool()
        await pool.load_from_db()

        proxy = await pool.get_proxy_for_account(account_id)
        if proxy:
            telethon_proxy = proxy.to_telethon_format()

        # При ошибке
        await pool.mark_proxy_failed(proxy)
        new_proxy = await pool.get_new_proxy_for_account(account_id)
    """

    # Константы
    CHECK_TIMEOUT = 15  # секунд
    MAX_CONSECUTIVE_FAILS = 3  # после этого прокси помечается unhealthy
    CHECK_INTERVAL = 300  # секунд между проверками (5 мин)

    def __init__(self):
        self._proxies: Dict[str, ProxyInfo] = {}  # key = host:port:user
        self._account_bindings: Dict[int, str] = {}  # account_id -> proxy_key
        self._lock = asyncio.Lock()
        self._check_task: Optional[asyncio.Task] = None
        self._running = False

    def _make_key(self, proxy: ProxyInfo) -> str:
        """Создать уникальный ключ для прокси."""
        return f"{proxy.host}:{proxy.port}:{proxy.username or ''}"

    async def add_proxy(
        self,
        proxy_type: str,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_id: Optional[int] = None,
        max_accounts: int = 6,
        country: Optional[str] = None,
    ) -> ProxyInfo:
        """Добавить прокси в пул."""
        proxy = ProxyInfo(
            proxy_type=proxy_type,
            host=host,
            port=port,
            username=username,
            password=password,
            db_id=db_id,
            max_accounts=max_accounts,
            country=country,
        )
        key = self._make_key(proxy)

        async with self._lock:
            if key not in self._proxies:
                self._proxies[key] = proxy
                logger.info(
                    f"[proxy_pool] Added proxy: {proxy.masked_credentials} (country={country}, max={max_accounts})"
                )
            else:
                # Обновляем пароль, db_id, max_accounts, country если изменились
                existing = self._proxies[key]
                existing.password = password
                existing.db_id = db_id
                existing.max_accounts = max_accounts
                existing.country = country
                proxy = existing

        return proxy

    async def remove_proxy(self, proxy: ProxyInfo) -> bool:
        """Удалить прокси из пула."""
        key = self._make_key(proxy)

        async with self._lock:
            if key in self._proxies:
                del self._proxies[key]
                # Удаляем привязки
                for acc_id, pkey in list(self._account_bindings.items()):
                    if pkey == key:
                        del self._account_bindings[acc_id]
                logger.info(f"[proxy_pool] Removed proxy: {proxy.masked_credentials}")
                return True
        return False

    def _count_accounts_on_proxy(self, proxy_key: str) -> int:
        """Подсчитать количество аккаунтов на прокси."""
        return sum(1 for pk in self._account_bindings.values() if pk == proxy_key)

    # @delete
    # def _is_proxy_available(self, proxy: ProxyInfo) -> bool:
    #     """Проверить, доступен ли прокси для назначения."""
    #     if not (proxy.is_healthy or proxy.status == ProxyStatus.UNKNOWN):
    #         return False

    #     # Если max_accounts = 0, лимита нет
    #     if proxy.max_accounts == 0:
    #         return True

    #     key = self._make_key(proxy)
    #     current_count = self._count_accounts_on_proxy(key)
    #     return current_count < proxy.max_accounts
    # @delete
    def _is_proxy_available(self, proxy: ProxyInfo) -> bool:
        # """Проверить, доступен ли прокси для назначения."""
        # ДОБАВИТЬ проверку флага активности из БД
        # Для этого нужно передавать флаг is_active из Proxy в ProxyInfo

        # Исправленная проверка:
        # 1. Прокси должен быть активен в БД (ручной или автоматический флаг)
        # 2. И быть healthy/unknown в пуле
        # 3. И не превышать лимит аккаунтов

        # В ProxyInfo нужно добавить поле is_active
        if hasattr(proxy, "is_active") and not proxy.is_active:
            return False

        if not (proxy.is_healthy or proxy.status == ProxyStatus.UNKNOWN):
            return False

        # Если max_accounts = 0, лимита нет
        if proxy.max_accounts == 0:
            return True

        key = self._make_key(proxy)
        current_count = self._count_accounts_on_proxy(key)
        return current_count < proxy.max_accounts

    async def get_proxy_for_account(
        self, account_id: int, account_country: Optional[str] = None
    ) -> Optional[ProxyInfo]:
        """
        Получить прокси для аккаунта (sticky-привязка).

        Логика:
        1. Если аккаунт уже привязан к прокси и он здоров - вернёт его
        2. Если указана страна - ищет прокси из этой страны с учётом лимита (5-6 акков)
        3. Если нет подходящего по стране - берёт любой свободный
        4. Лимит: max_accounts аккаунтов на 1 прокси (по умолчанию 6)

        Args:
            account_id: ID аккаунта
            account_country: ISO код страны аккаунта (опционально)

        Returns:
            ProxyInfo или None если нет доступных
        """
        async with self._lock:
            # Проверяем существующую привязку
            if account_id in self._account_bindings:
                key = self._account_bindings[account_id]
                if key in self._proxies:
                    proxy = self._proxies[key]
                    if proxy.is_healthy or proxy.status == ProxyStatus.UNKNOWN:
                        logger.debug(
                            f"[proxy_pool] Using sticky proxy for account {account_id}: {proxy.masked_credentials}"
                        )
                        return proxy
                    # Прокси плохой - удаляем привязку
                    del self._account_bindings[account_id]

            # Получаем все доступные прокси (здоровые и с местом)
            available_proxies = [
                p for p in self._proxies.values() if self._is_proxy_available(p)
            ]

            if not available_proxies:
                logger.warning(
                    f"[proxy_pool] No available proxies for account {account_id}"
                )
                return None

            selected_proxy = None

            # 1) Если указана страна - ищем прокси из этой страны
            if account_country:
                country_proxies = [
                    p
                    for p in available_proxies
                    if p.country and p.country.upper() == account_country.upper()
                ]

                if country_proxies:
                    # Сортируем по загрузке (наименее загруженный первым)
                    country_proxies.sort(
                        key=lambda p: self._count_accounts_on_proxy(self._make_key(p))
                    )
                    selected_proxy = country_proxies[0]
                    logger.info(
                        f"[proxy_pool] Found matching country proxy for {account_country}: {selected_proxy.masked_credentials}"
                    )
                else:
                    logger.warning(
                        f"[proxy_pool] No proxy for country {account_country}, using fallback"
                    )

            # 2) Если не нашли по стране - берём любой свободный
            if selected_proxy is None:
                # Сортируем по загрузке
                available_proxies.sort(
                    key=lambda p: self._count_accounts_on_proxy(self._make_key(p))
                )
                selected_proxy = available_proxies[0]
                logger.info(
                    f"[proxy_pool] Using fallback proxy: {selected_proxy.masked_credentials}"
                )

            # Привязываем
            key = self._make_key(selected_proxy)
            self._account_bindings[account_id] = key
            count = self._count_accounts_on_proxy(key)
            logger.info(
                f"[proxy_pool] Assigned proxy to account {account_id}: {selected_proxy.masked_credentials} ({count}/{selected_proxy.max_accounts})"
            )

            return selected_proxy

    async def get_new_proxy_for_account(
        self, account_id: int, account_country: Optional[str] = None
    ) -> Optional[ProxyInfo]:
        """
        Получить НОВЫЙ прокси для аккаунта (после ошибки).

        Исключает текущий привязанный прокси и учитывает:
        1. Страну аккаунта (приоритет)
        2. Лимит аккаунтов на прокси (5-6)
        3. Fallback на любой свободный

        Args:
            account_id: ID аккаунта
            account_country: ISO код страны аккаунта (опционально)

        Returns:
            ProxyInfo или None
        """
        async with self._lock:
            # Получаем текущий прокси чтобы исключить
            exclude_key = self._account_bindings.get(account_id)

            # Удаляем старую привязку (освобождает слот)
            if account_id in self._account_bindings:
                del self._account_bindings[account_id]

            # Получаем все доступные прокси, КРОМЕ текущего
            available_proxies = [
                p
                for p in self._proxies.values()
                if self._is_proxy_available(p) and self._make_key(p) != exclude_key
            ]

            if not available_proxies:
                logger.warning(
                    f"[proxy_pool] No alternative proxies for account {account_id}"
                )
                return None

            selected_proxy = None

            # 1) Если указана страна - ищем прокси из этой страны
            if account_country:
                country_proxies = [
                    p
                    for p in available_proxies
                    if p.country and p.country.upper() == account_country.upper()
                ]

                if country_proxies:
                    country_proxies.sort(
                        key=lambda p: self._count_accounts_on_proxy(self._make_key(p))
                    )
                    selected_proxy = country_proxies[0]
                    logger.info(
                        f"[proxy_pool] Found new country proxy for {account_country}: {selected_proxy.masked_credentials}"
                    )

            # 2) Если не нашли по стране - берём любой свободный
            if selected_proxy is None:
                available_proxies.sort(
                    key=lambda p: self._count_accounts_on_proxy(self._make_key(p))
                )
                selected_proxy = available_proxies[0]

            # Привязываем
            key = self._make_key(selected_proxy)
            self._account_bindings[account_id] = key
            count = self._count_accounts_on_proxy(key)
            logger.info(
                f"[proxy_pool] Assigned NEW proxy to account {account_id}: {selected_proxy.masked_credentials} ({count}/{selected_proxy.max_accounts})"
            )

            return selected_proxy

    async def mark_proxy_failed(self, proxy: ProxyInfo) -> None:
        """Отметить прокси как неудачный."""
        key = self._make_key(proxy)

        async with self._lock:
            if key in self._proxies:
                p = self._proxies[key]
                p.fail_count += 1
                p.consecutive_fails += 1

                if p.consecutive_fails >= self.MAX_CONSECUTIVE_FAILS:
                    p.status = ProxyStatus.UNHEALTHY
                    logger.warning(
                        f"[proxy_pool] Proxy marked UNHEALTHY: {p.masked_credentials} (fails={p.consecutive_fails})"
                    )

    async def mark_proxy_success(self, proxy: ProxyInfo) -> None:
        """Отметить прокси как успешный."""
        key = self._make_key(proxy)

        async with self._lock:
            if key in self._proxies:
                p = self._proxies[key]
                p.success_count += 1
                p.consecutive_fails = 0
                p.status = ProxyStatus.HEALTHY

    async def check_proxy(self, proxy: ProxyInfo) -> bool:
        """
        Проверить работоспособность прокси.

        Returns:
            True если прокси рабочий
        """
        import aiohttp

        proxy.status = ProxyStatus.CHECKING
        start_time = time.time()

        try:
            # Для SOCKS используем python-socks
            if proxy.proxy_type.lower() in ("socks5", "socks4"):
                try:
                    from python_socks.async_.asyncio.v2 import Proxy as SocksProxy
                    from python_socks import ProxyType as SocksProxyType
                except ImportError:
                    logger.error("[proxy_pool] python-socks not installed!")
                    return False

                ptype = (
                    SocksProxyType.SOCKS5
                    if proxy.proxy_type.lower() == "socks5"
                    else SocksProxyType.SOCKS4
                )
                socks_proxy = SocksProxy(
                    proxy_type=ptype,
                    host=proxy.host,
                    port=proxy.port,
                    username=proxy.username,
                    password=proxy.password,
                )

                sock = await asyncio.wait_for(
                    socks_proxy.connect(dest_host="api.ipify.org", dest_port=80),
                    timeout=self.CHECK_TIMEOUT,
                )

                try:
                    request = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n"
                    await sock.write_all(request)

                    response = b""
                    while True:
                        chunk = await sock.read(1024)
                        if not chunk:
                            break
                        response += chunk

                    response_text = response.decode("utf-8", errors="ignore")
                    if (
                        "HTTP/1.1 200" in response_text
                        or "HTTP/1.0 200" in response_text
                    ):
                        body = response_text.split("\r\n\r\n")[-1].strip()
                        proxy.last_check_ip = body
                        proxy.latency_ms = int((time.time() - start_time) * 1000)
                        proxy.last_check_time = time.time()
                        proxy.status = ProxyStatus.HEALTHY
                        proxy.consecutive_fails = 0
                        return True
                finally:
                    await sock.close()

            else:
                # HTTP/HTTPS прокси
                timeout = aiohttp.ClientTimeout(total=self.CHECK_TIMEOUT)

                proxy_url = f"http://{proxy.host}:{proxy.port}"
                if proxy.username:
                    proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        "https://api.ipify.org", proxy=proxy_url
                    ) as resp:
                        if resp.status == 200:
                            ip = (await resp.text()).strip()
                            proxy.last_check_ip = ip
                            proxy.latency_ms = int((time.time() - start_time) * 1000)
                            proxy.last_check_time = time.time()
                            proxy.status = ProxyStatus.HEALTHY
                            proxy.consecutive_fails = 0
                            return True

        except asyncio.TimeoutError:
            logger.warning(
                f"[proxy_pool] Proxy check timeout: {proxy.masked_credentials}"
            )
        except Exception as e:
            logger.warning(
                f"[proxy_pool] Proxy check failed: {proxy.masked_credentials} - {type(e).__name__}"
            )

        proxy.status = ProxyStatus.UNHEALTHY
        proxy.consecutive_fails += 1
        proxy.last_check_time = time.time()
        return False

    async def check_all_proxies(self) -> Tuple[int, int]:
        """
        Проверить все прокси.

        Returns:
            (healthy_count, unhealthy_count)
        """
        proxies = list(self._proxies.values())
        healthy = 0
        unhealthy = 0

        for proxy in proxies:
            if await self.check_proxy(proxy):
                healthy += 1
            else:
                unhealthy += 1

        logger.info(
            f"[proxy_pool] Check complete: {healthy} healthy, {unhealthy} unhealthy"
        )
        return healthy, unhealthy

    def get_stats(self) -> ProxyPoolStats:
        """Получить статистику пула."""
        stats = ProxyPoolStats(
            total=len(self._proxies),
            last_check_time=(
                datetime.now()
                if any(p.last_check_time for p in self._proxies.values())
                else None
            ),
        )

        for proxy in self._proxies.values():
            if proxy.status == ProxyStatus.HEALTHY:
                stats.healthy += 1
            elif proxy.status == ProxyStatus.UNHEALTHY:
                stats.unhealthy += 1
            elif proxy.status == ProxyStatus.CHECKING:
                stats.checking += 1
            else:
                stats.unknown += 1

        return stats

    async def start_background_checker(self, interval: int = None) -> None:
        """Запустить фоновую проверку прокси."""
        if self._running:
            return

        self._running = True
        interval = interval or self.CHECK_INTERVAL

        async def checker():
            while self._running:
                try:
                    await self.check_all_proxies()
                except Exception as e:
                    logger.exception(f"[proxy_pool] Background check error: {e}")

                await asyncio.sleep(interval)

        self._check_task = asyncio.create_task(checker())
        logger.info(f"[proxy_pool] Background checker started (interval={interval}s)")

    async def stop_background_checker(self) -> None:
        """Остановить фоновую проверку."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None
        logger.info("[proxy_pool] Background checker stopped")

    def clear(self) -> None:
        """Очистить пул."""
        self._proxies.clear()
        self._account_bindings.clear()


# Глобальный экземпляр пула
_proxy_pool: Optional[ProxyPool] = None


def get_proxy_pool() -> ProxyPool:
    """Получить глобальный экземпляр пула прокси."""
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool()
    return _proxy_pool


async def load_proxies_from_db() -> int:
    """
    Загрузить прокси из БД в пул.

    Returns:
        Количество загруженных прокси
    """
    from db.session import get_session
    from services import proxy_service

    pool = get_proxy_pool()
    count = 0

    async with get_session() as session:
        proxies = await proxy_service.get_active_proxies(session)

        for p in proxies:
            # print("PROXY ", p)
            await pool.add_proxy(
                proxy_type=p.proxy_type.value,
                host=p.host,
                port=p.port,
                username=p.username,
                password=p.password,
                db_id=p.id,
                max_accounts=p.max_accounts,
                country=p.country,
            )
            count += 1

    logger.info(f"[proxy_pool] Loaded {count} proxies from DB")
    return count


async def sync_proxy_status_to_db() -> None:
    """Синхронизировать статусы прокси обратно в БД."""
    from db.session import get_session
    from services import proxy_service

    pool = get_proxy_pool()

    async with get_session() as session:
        for proxy in pool._proxies.values():
            if proxy.db_id:
                await proxy_service.update_proxy_check_result(
                    session,
                    proxy.db_id,
                    is_working=proxy.is_healthy,
                    ip=proxy.last_check_ip,
                    latency_ms=proxy.latency_ms,
                    auto_commit=False,
                )
        await session.commit()

    logger.info("[proxy_pool] Synced proxy statuses to DB")
