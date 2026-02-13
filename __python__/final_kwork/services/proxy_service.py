"""
Сервис для управления прокси-серверами.

Функции:
- Парсинг прокси из различных форматов
- Проверка работоспособности прокси
- CRUD операции
- Назначение прокси на аккаунты (round-robin)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Импорт python-socks для проверки SOCKS прокси
try:
    from python_socks.async_.asyncio.v2 import Proxy as SocksProxy
    from python_socks import ProxyType as SocksProxyType

    PYTHON_SOCKS_AVAILABLE = True
except ImportError:
    PYTHON_SOCKS_AVAILABLE = False
    SocksProxy = None
    SocksProxyType = None

from db.models import Proxy, ProxyType, Account

logger = logging.getLogger(__name__)

# Проверяем доступность python-socks при старте
if not PYTHON_SOCKS_AVAILABLE:
    logger.error(
        "python-socks is NOT installed! SOCKS proxy checks will fail. Run: pip install python-socks"
    )

# Таймаут проверки прокси (секунды)
PROXY_CHECK_TIMEOUT = 15
# URL для проверки IP
CHECK_URL = "https://api.ipify.org"
# URL для определения страны по IP
GEO_URL = "http://ip-api.com/json/{ip}?fields=countryCode"


async def get_country_by_ip(ip: str) -> Optional[str]:
    """
    Определить страну по IP через бесплатный API.

    Returns:
        ISO 3166-1 alpha-2 код страны (RU, US, DE...) или None
    """
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GEO_URL.format(ip=ip)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("countryCode")
    except Exception as e:
        logger.warning(f"Failed to get country for IP {ip}: {e}")
    return None


# Флаги стран (emoji)
COUNTRY_FLAGS = {
    "RU": "🇷🇺",
    "US": "🇺🇸",
    "DE": "🇩🇪",
    "NL": "🇳🇱",
    "GB": "🇬🇧",
    "FR": "🇫🇷",
    "CA": "🇨🇦",
    "UA": "🇺🇦",
    "PL": "🇵🇱",
    "IT": "🇮🇹",
    "ES": "🇪🇸",
    "SE": "🇸🇪",
    "NO": "🇳🇴",
    "FI": "🇫🇮",
    "DK": "🇩🇰",
    "CH": "🇨🇭",
    "AT": "🇦🇹",
    "BE": "🇧🇪",
    "CZ": "🇨🇿",
    "PT": "🇵🇹",
    "JP": "🇯🇵",
    "KR": "🇰🇷",
    "CN": "🇨🇳",
    "HK": "🇭🇰",
    "SG": "🇸🇬",
    "AU": "🇦🇺",
    "BR": "🇧🇷",
    "IN": "🇮🇳",
    "TR": "🇹🇷",
    "IL": "🇮🇱",
    "AE": "🇦🇪",
    "KZ": "🇰🇿",
    "BY": "🇧🇾",
    "LT": "🇱🇹",
    "LV": "🇱🇻",
    "EE": "🇪🇪",
    "MD": "🇲🇩",
    "GE": "🇬🇪",
    "AM": "🇦🇲",
    "AZ": "🇦🇿",
}

# Коды телефонов стран (prefix -> country code)
PHONE_COUNTRY_CODES = {
    "7": "RU",  # Россия
    "380": "UA",  # Украина
    "375": "BY",  # Беларусь
    "77": "KZ",  # Казахстан (77x)
    "1": "US",  # США/Канада
    "44": "GB",  # Великобритания
    "49": "DE",  # Германия
    "33": "FR",  # Франция
    "39": "IT",  # Италия
    "34": "ES",  # Испания
    "31": "NL",  # Нидерланды
    "48": "PL",  # Польша
    "420": "CZ",  # Чехия
    "43": "AT",  # Австрия
    "41": "CH",  # Швейцария
    "46": "SE",  # Швеция
    "47": "NO",  # Норвегия
    "45": "DK",  # Дания
    "358": "FI",  # Финляндия
    "32": "BE",  # Бельгия
    "351": "PT",  # Португалия
    "90": "TR",  # Турция
    "81": "JP",  # Япония
    "82": "KR",  # Южная Корея
    "86": "CN",  # Китай
    "852": "HK",  # Гонконг
    "65": "SG",  # Сингапур
    "61": "AU",  # Австралия
    "55": "BR",  # Бразилия
    "91": "IN",  # Индия
    "972": "IL",  # Израиль
    "971": "AE",  # ОАЭ
    "370": "LT",  # Литва
    "371": "LV",  # Латвия
    "372": "EE",  # Эстония
    "373": "MD",  # Молдова
    "374": "AM",  # Армения
    "994": "AZ",  # Азербайджан
    "995": "GE",  # Грузия
}


def get_country_by_phone(phone: Optional[str]) -> Optional[str]:
    """
    Определить страну по номеру телефона.

    Args:
        phone: Номер телефона (может начинаться с + или без)

    Returns:
        ISO код страны или None
    """
    if not phone:
        return None

    # Убираем + и пробелы
    phone = phone.lstrip("+").replace(" ", "").replace("-", "")

    # Проверяем от длинных кодов к коротким (чтобы 77 проверить раньше 7)
    for prefix in sorted(PHONE_COUNTRY_CODES.keys(), key=len, reverse=True):
        if phone.startswith(prefix):
            return PHONE_COUNTRY_CODES[prefix]

    return None


def get_country_flag(country_code: Optional[str]) -> str:
    """Получить флаг страны по коду."""
    if not country_code:
        return "🌍"
    return COUNTRY_FLAGS.get(country_code.upper(), "🏳️")


class ProxyParseResult:
    """Результат парсинга прокси."""

    def __init__(
        self,
        host: str,
        port: int,
        proxy_type: ProxyType = ProxyType.SOCKS5,
        username: Optional[str] = None,
        password: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.proxy_type = proxy_type
        self.username = username
        self.password = password
        self.error = error

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.host and self.port


def _parse_host_port(host_port: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Парсинг host:port с поддержкой IPv4 и IPv6.

    Форматы:
    - 192.168.1.1:8080 (IPv4)
    - [2001:db8::1]:8080 (IPv6 в квадратных скобках)
    - [::1]:1080

    Returns:
        (host, port) или (None, None) при ошибке
    """
    host_port = host_port.strip()

    # IPv6 в квадратных скобках: [ipv6]:port
    if host_port.startswith("["):
        # Ищем закрывающую скобку
        bracket_end = host_port.find("]")
        if bracket_end == -1:
            return None, None

        host = host_port[1:bracket_end]  # Без скобок

        # После ] должен быть :port
        remainder = host_port[bracket_end + 1 :]
        if not remainder.startswith(":"):
            return None, None

        try:
            port = int(remainder[1:])
            return host, port
        except ValueError:
            return None, None

    # IPv4 или hostname: host:port
    if ":" not in host_port:
        return None, None

    # Для IPv4/hostname просто rsplit по последнему двоеточию
    parts = host_port.rsplit(":", 1)
    host = parts[0]

    try:
        port = int(parts[1])
        return host, port
    except ValueError:
        return None, None


def parse_proxy_line(line: str) -> ProxyParseResult:
    """
    Парсинг строки прокси в различных форматах.

    Поддерживаемые форматы:
    - host:port (IPv4)
    - host:port:user:pass (новый формат)
    - [ipv6]:port
    - user:pass@host:port
    - user:pass@[ipv6]:port
    - socks5://host:port
    - socks5://[ipv6]:port
    - socks5://user:pass@host:port
    - http://host:port
    - http://user:pass@host:port

    Returns:
        ProxyParseResult с данными или ошибкой
    """
    line = line.strip()
    if not line:
        return ProxyParseResult("", 0, error="Пустая строка")

    proxy_type = ProxyType.HTTP  # default
    username = None
    password = None
    host = None
    port = None

    # Проверяем тип прокси в конце строки (формат: host:port TYPE или user:pass@host:port TYPE)
    type_suffix_map = {
        "socks5": ProxyType.SOCKS5,
        "http": ProxyType.HTTP,
        "https": ProxyType.HTTPS,
    }

    parts = line.rsplit(None, 1)  # Разделяем по последнему пробелу
    if len(parts) == 2:
        potential_type = parts[1].lower()
        if potential_type in type_suffix_map:
            proxy_type = type_suffix_map[potential_type]
            line = parts[0]  # Убираем тип из строки

    # Пробуем распарсить как URL
    if "://" in line:
        try:
            parsed = urlparse(line)
            scheme = parsed.scheme.lower()

            # Определяем тип
            if scheme in ("socks5", "socks5h"):
                proxy_type = ProxyType.SOCKS5
            elif scheme == "http":
                proxy_type = ProxyType.HTTP
            elif scheme == "https":
                proxy_type = ProxyType.HTTPS
            else:
                return ProxyParseResult(
                    "", 0, error=f"Неподдерживаемая схема: {scheme}"
                )

            host = parsed.hostname
            port = parsed.port
            username = parsed.username
            password = parsed.password

        except Exception as e:
            return ProxyParseResult("", 0, error=f"Ошибка парсинга URL: {e}")
    else:
        # Проверяем формат host:port:user:pass (4 части через двоеточие, без @)
        if "@" not in line and not line.startswith("["):
            colon_parts = line.split(":")
            if len(colon_parts) == 4:
                # Формат: host:port:user:pass
                host = colon_parts[0]
                try:
                    port = int(colon_parts[1])
                    username = colon_parts[2]
                    password = colon_parts[3]
                except ValueError:
                    return ProxyParseResult("", 0, error="Некорректный порт")
            elif len(colon_parts) == 2:
                # Формат: host:port
                host, port = _parse_host_port(line)
                if host is None:
                    return ProxyParseResult(
                        "", 0, error="Некорректный формат host:port"
                    )
            else:
                return ProxyParseResult(
                    "",
                    0,
                    error="Некорректный формат (ожидается host:port или host:port:user:pass)",
                )
        elif "@" in line:
            # Формат: user:pass@host:port
            auth_part, host_part = line.rsplit("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                username = auth_part

            # Парсим host:port с поддержкой IPv6
            host, port = _parse_host_port(host_part)
            if host is None:
                return ProxyParseResult("", 0, error="Некорректный формат host:port")
        else:
            # IPv6 формат
            host, port = _parse_host_port(line)
            if host is None:
                return ProxyParseResult("", 0, error="Некорректный формат host:port")

    # Валидация
    if not host:
        return ProxyParseResult("", 0, error="Отсутствует хост")
    if not port or port < 1 or port > 65535:
        return ProxyParseResult("", 0, error=f"Некорректный порт: {port}")

    return ProxyParseResult(
        host=host,
        port=port,
        proxy_type=proxy_type,
        username=username,
        password=password,
    )


def parse_proxy_list(text: str) -> Tuple[List[ProxyParseResult], List[str]]:
    """
    Парсинг списка прокси из текста (каждая строка = один прокси).

    Returns:
        (valid_proxies, errors)
    """
    valid = []
    errors = []

    for i, line in enumerate(text.strip().split("\n"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        result = parse_proxy_line(line)
        if result.is_valid:
            valid.append(result)
        else:
            errors.append(f"Строка {i}: {result.error} ({line})")

    return valid, errors


async def check_proxy(proxy: Proxy) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Проверить работоспособность прокси.

    Returns:
        (is_working, external_ip, latency_ms)
    """
    start_time = asyncio.get_event_loop().time()

    # Для SOCKS5 используем python-socks напрямую (более надёжно чем aiohttp-socks)
    if proxy.proxy_type == ProxyType.SOCKS5:
        if not PYTHON_SOCKS_AVAILABLE:
            logger.error(
                "python-socks not installed! Cannot check SOCKS proxy. Run: pip install python-socks"
            )
            return False, None, None

        try:
            socks_proxy = SocksProxy(
                proxy_type=SocksProxyType.SOCKS5,
                host=proxy.host,
                port=proxy.port,
                username=proxy.username,
                password=proxy.password,
            )

            # Подключаемся к api.ipify.org через прокси
            sock = await asyncio.wait_for(
                socks_proxy.connect(dest_host="api.ipify.org", dest_port=80),
                timeout=PROXY_CHECK_TIMEOUT,
            )

            try:
                # Отправляем HTTP запрос вручную
                request = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n"
                await sock.write_all(request)

                response = b""
                while True:
                    chunk = await sock.read(1024)
                    if not chunk:
                        break
                    response += chunk

                # Парсим ответ
                response_text = response.decode("utf-8", errors="ignore")
                if "HTTP/1.1 200" in response_text or "HTTP/1.0 200" in response_text:
                    # Извлекаем IP из body
                    body = response_text.split("\r\n\r\n")[-1].strip()
                    latency = int((asyncio.get_event_loop().time() - start_time) * 1000)
                    return True, body, latency
            finally:
                await sock.close()

        except asyncio.TimeoutError:
            logger.warning(f"Proxy check timeout: {proxy}")
        except Exception as e:
            logger.warning(f"Proxy check failed: {proxy} - {type(e).__name__}: {e}")

        return False, None, None

    # HTTP/HTTPS прокси через aiohttp
    try:
        timeout = aiohttp.ClientTimeout(total=PROXY_CHECK_TIMEOUT)
        connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            if proxy.username:
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            async with session.get(CHECK_URL, proxy=proxy_url) as resp:
                if resp.status == 200:
                    ip = (await resp.text()).strip()
                    latency = int((asyncio.get_event_loop().time() - start_time) * 1000)
                    return True, ip, latency

    except asyncio.TimeoutError:
        logger.warning(f"Proxy check timeout: {proxy}")
    except Exception as e:
        logger.warning(f"Proxy check failed: {proxy} - {type(e).__name__}: {e}")

    return False, None, None


# =============================================================================
# CRUD операции
# =============================================================================


async def get_all_proxies(session: AsyncSession) -> List[Proxy]:
    """Получить все прокси."""
    result = await session.execute(
        select(Proxy).order_by(Proxy.is_active.desc(), Proxy.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_proxies(session: AsyncSession) -> List[Proxy]:
    """Получить только активные прокси."""
    result = await session.execute(
        select(Proxy)
        .where(Proxy.is_active.is_(True))
        .order_by(Proxy.latency_ms.nullslast())
    )
    proxys = list(result.scalars().all())
    print("LEN PROXY: ", len(proxys))
    return proxys


async def get_proxy_by_id(session: AsyncSession, proxy_id: int) -> Optional[Proxy]:
    """Получить прокси по ID."""
    result = await session.execute(select(Proxy).where(Proxy.id == proxy_id))
    return result.scalar_one_or_none()


async def get_proxy_with_accounts(
    session: AsyncSession, proxy_id: int
) -> Optional[Proxy]:
    """Получить прокси с загруженными аккаунтами."""
    result = await session.execute(
        select(Proxy).options(selectinload(Proxy.accounts)).where(Proxy.id == proxy_id)
    )
    return result.scalar_one_or_none()


async def find_proxy(
    session: AsyncSession,
    host: str,
    port: int,
    proxy_type: ProxyType,
    username: Optional[str] = None,
) -> Optional[Proxy]:
    """Найти существующий прокси по параметрам."""
    query = select(Proxy).where(
        Proxy.host == host, Proxy.port == port, Proxy.proxy_type == proxy_type
    )
    if username:
        query = query.where(Proxy.username == username)
    else:
        query = query.where(Proxy.username.is_(None))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_or_update_proxy(
    session: AsyncSession, parsed: ProxyParseResult
) -> Tuple[Proxy, bool]:
    """
    Создать или обновить прокси (upsert).

    Returns:
        (proxy, is_new)
    """
    existing = await find_proxy(
        session, parsed.host, parsed.port, parsed.proxy_type, parsed.username
    )

    if existing:
        # Обновляем пароль если изменился
        if parsed.password and existing.password != parsed.password:
            existing.password = parsed.password
            existing.updated_at = datetime.utcnow()
        return existing, False

    proxy = Proxy(
        host=parsed.host,
        port=parsed.port,
        proxy_type=parsed.proxy_type,
        username=parsed.username,
        password=parsed.password,
        is_active=True,
    )
    session.add(proxy)
    await session.flush()

    return proxy, True


async def import_proxies(
    session: AsyncSession, text: str, default_type: Optional[ProxyType] = None
) -> Tuple[int, int, List[str]]:
    """
    Импортировать список прокси из текста.

    Args:
        session: AsyncSession
        text: Текст со списком прокси
        default_type: Тип прокси по умолчанию (если не указан в строке)

    Returns:
        (new_count, updated_count, errors)
    """
    parsed_list, parse_errors = parse_proxy_list(text)

    new_count = 0
    updated_count = 0

    for parsed in parsed_list:
        # Применяем default_type если тип не был явно указан (остался SOCKS5 по умолчанию)
        if default_type is not None:
            parsed.proxy_type = default_type

        proxy, is_new = await create_or_update_proxy(session, parsed)
        if is_new:
            new_count += 1
        else:
            updated_count += 1

    await session.commit()

    return new_count, updated_count, parse_errors


# @delete
# async def update_proxy_check_result(
#     session: AsyncSession,
#     proxy_id: int,
#     is_working: bool,
#     ip: Optional[str] = None,
#     latency_ms: Optional[int] = None,
#     country: Optional[str] = None,
#     auto_commit: bool = True
# ) -> None:
#     """Обновить результаты проверки прокси."""
#     proxy = await get_proxy_by_id(session, proxy_id)
#     if not proxy:
#         return

#     proxy.last_checked_at = datetime.utcnow()

#     # Важно: результаты проверки НЕ должны автоматически выключать прокси навсегда,
#     # иначе при временных проблемах сети/проверяющего сервиса "пропадают" все прокси из пула.
#     if is_working:
#         proxy.last_check_ip = ip
#         proxy.latency_ms = latency_ms
#         if country:
#             proxy.country = country
#         proxy.success_count += 1
#         proxy.fail_count = 0  # Сброс при успехе
#         # proxy.is_active НЕ трогаем: это ручной флаг
#     else:
#         proxy.fail_count += 1
#         # proxy.is_active НЕ трогаем: это ручной флаг


#     if auto_commit:
#         await session.commit()
# @delete
async def update_proxy_check_result(
    session: AsyncSession,
    proxy_id: int,
    is_working: bool,
    ip: Optional[str] = None,
    latency_ms: Optional[int] = None,
    country: Optional[str] = None,
    auto_commit: bool = True,
) -> None:
    """Обновить результаты проверки прокси."""
    proxy = await get_proxy_by_id(session, proxy_id)
    if not proxy:
        return

    proxy.last_checked_at = datetime.utcnow()

    # ВАЖНОЕ ИСПРАВЛЕНИЕ: Автоматически отключаем прокси только если слишком много фейлов подряд
    if is_working:
        proxy.last_check_ip = ip
        proxy.latency_ms = latency_ms
        if country:
            proxy.country = country
        proxy.success_count += 1
        proxy.fail_count = 0  # Сброс при успехе
        proxy.consecutive_fails = 0  # НОВОЕ: сбрасываем счётчик
        proxy.is_active = True  # ВОЗВРАЩАЕМ в актив, если был отключен автоматически
    else:
        proxy.fail_count += 1
        proxy.consecutive_fails = getattr(proxy, "consecutive_fails", 0) + 1

        # Автоматически отключаем только после 5 неудач подряд
        if proxy.consecutive_fails >= 5:
            proxy.is_active = False
            logger.warning(
                f"Proxy #{proxy_id} auto-disabled after {proxy.consecutive_fails} consecutive fails"
            )
        # НЕ УДАЛЯЕМ из БД никогда!

    if auto_commit:
        await session.commit()


async def check_all_proxies(
    session: AsyncSession, only_active: bool = False
) -> Tuple[int, int]:
    """
    Проверить все прокси.

    Returns:
        (working_count, failed_count)
    """
    if only_active:
        proxies = await get_active_proxies(session)
    else:
        proxies = await get_all_proxies(session)

    working = 0
    failed = 0

    # Проверяем последовательно чтобы избежать race condition с сессией БД
    for proxy in proxies:
        is_ok, ip, latency = await check_proxy(proxy)

        # Определяем страну по IP если прокси рабочий
        country = None
        if is_ok and ip:
            country = await get_country_by_ip(ip)

        await update_proxy_check_result(
            session, proxy.id, is_ok, ip, latency, country=country, auto_commit=False
        )
        if is_ok:
            working += 1
        else:
            failed += 1

    await session.commit()

    return working, failed


async def delete_proxy(session: AsyncSession, proxy_id: int) -> bool:
    """
    Удалить прокси. Отвязывает от аккаунтов.

    Returns:
        True если удалён
    """
    proxy = await get_proxy_with_accounts(session, proxy_id)
    if not proxy:
        return False

    # Отвязываем от аккаунтов
    for acc in proxy.accounts:
        acc.proxy_id = None

    await session.delete(proxy)
    await session.commit()

    return True


async def toggle_proxy(session: AsyncSession, proxy_id: int) -> Optional[bool]:
    """
    Переключить активность прокси.

    Returns:
        Новое состояние или None если не найден
    """
    proxy = await get_proxy_by_id(session, proxy_id)
    if not proxy:
        return None

    proxy.is_active = not proxy.is_active
    await session.commit()

    return proxy.is_active


# =============================================================================
# Назначение прокси на аккаунты
# =============================================================================


async def get_accounts_on_proxy(session: AsyncSession, proxy_id: int) -> int:
    """Количество аккаунтов на прокси."""
    result = await session.execute(
        select(func.count(Account.id)).where(Account.proxy_id == proxy_id)
    )
    return result.scalar() or 0


async def get_best_proxy_for_account(
    session: AsyncSession, account_country: Optional[str] = None
) -> Optional[Proxy]:
    """
    Подобрать лучший прокси для аккаунта.

    Логика выбора:
    1. Если указана страна аккаунта — ищем прокси из этой страны (приоритет)
    2. Если нет прокси для страны — берём любой доступный прокси из БД
    3. Лимит: 1 прокси на 5-6 аккаунтов (max_accounts)

    Args:
        session: AsyncSession
        account_country: ISO код страны аккаунта (опционально)

    Returns:
        Прокси или None если нет доступных вообще
    """
    proxies = await get_active_proxies(session)

    # Если указана страна — сначала ищем прокси из этой страны
    if account_country:
        for proxy in proxies:
            if proxy.country and proxy.country.upper() == account_country.upper():
                if proxy.max_accounts == 0:
                    return proxy
                count = await get_accounts_on_proxy(session, proxy.id)
                if count < proxy.max_accounts:
                    logger.info(
                        f"Found matching country proxy: {proxy} for {account_country}"
                    )
                    return proxy
        # Нет прокси для этой страны — используем fallback (любой доступный)
        logger.warning(
            f"No proxy found for country {account_country}, using any available proxy"
        )

    # Берём любой доступный прокси (fallback или если страна не определена)
    for proxy in proxies:
        if proxy.max_accounts == 0:
            return proxy

        count = await get_accounts_on_proxy(session, proxy.id)
        if count < proxy.max_accounts:
            return proxy

    return None


async def assign_proxy_to_account(
    session: AsyncSession, account_id: int, proxy_id: Optional[int] = None
) -> Optional[Proxy]:
    """
    Назначить прокси на аккаунт.

    Логика:
    - Если proxy_id указан — назначает этот прокси
    - Если нет — автоматически выбирает прокси по стране аккаунта (по номеру телефона)

    Args:
        account_id: ID аккаунта
        proxy_id: ID прокси (если None - выберет автоматически)

    Returns:
        Назначенный прокси или None
    """
    # Получаем аккаунт
    result = await session.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        return None

    if proxy_id:
        proxy = await get_proxy_by_id(session, proxy_id)
        if not proxy or not proxy.is_active:
            return None
    else:
        # Определяем страну аккаунта по номеру телефона
        account_country = get_country_by_phone(account.phone)
        if account_country:
            logger.info(
                f"Account {account_id} country detected: {account_country} (phone: {account.phone})"
            )
        proxy = await get_best_proxy_for_account(
            session, account_country=account_country
        )

    if proxy:
        account.proxy_id = proxy.id
        await session.commit()

    return proxy


async def unassign_proxy_from_account(session: AsyncSession, account_id: int) -> bool:
    """Отвязать прокси от аккаунта."""
    # Получаем аккаунт
    result = await session.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        return False

    account.proxy_id = None
    await session.commit()
    return True


async def get_proxy_stats(session: AsyncSession) -> dict:
    """Получить статистику по прокси."""
    proxies = await get_all_proxies(session)

    total = len(proxies)
    active = sum(1 for p in proxies if p.is_active)
    inactive = total - active

    # Считаем аккаунты с прокси одним запросом
    result = await session.execute(
        select(func.count(Account.id)).where(Account.proxy_id.isnot(None))
    )
    total_accounts = result.scalar() or 0

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "accounts_with_proxy": total_accounts,
    }
