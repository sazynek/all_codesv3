"""
Сервис импорта Telethon .session файлов.
Совместимость с Telethon 2.0.
"""

import asyncio
import json
import logging
import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

from services.telethon_adapter import (
    TelegramClient,
    AuthKeyUnregisteredError,
    SessionPasswordNeededError,
    get_user_premium,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Account, AccountStatus, StorageType
from services import proxy_service

logger = logging.getLogger(__name__)

# Лимит размера файла (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Директории хранения
STORAGE_BASE = "./storage"
INBOX_DIR = f"{STORAGE_BASE}/inbox"
SESSIONS_DIR = f"{STORAGE_BASE}/sessions"
TDATA_DIR = f"{STORAGE_BASE}/tdata"


@dataclass
class ApiCredentials:
    """API credentials для аккаунта."""

    api_id: int
    api_hash: str
    source: str = "json"  # "json" или "env"
    json_path: Optional[str] = None  # Путь к JSON файлу, откуда взяты credentials


@dataclass
class DeviceFingerprint:
    """Device fingerprint для стабильности сессии."""

    device_model: Optional[str] = None
    system_version: Optional[str] = None
    app_version: Optional[str] = None
    lang_code: Optional[str] = None
    system_lang_code: Optional[str] = None

    def is_valid(self) -> bool:
        """Проверить, есть ли хотя бы базовые данные."""
        return bool(self.device_model or self.app_version)

    @classmethod
    def default_android(cls) -> "DeviceFingerprint":
        """Дефолтный Android fingerprint (Samsung)."""
        return cls(
            device_model="Samsung SM-S918B",
            system_version="SDK 34",
            app_version="10.14.5 (5447)",
            lang_code="en",
            system_lang_code="en",
        )

    @classmethod
    def default_desktop(cls) -> "DeviceFingerprint":
        """Дефолтный TDesktop fingerprint."""
        return cls(
            device_model="Desktop",
            system_version="Windows 11",
            app_version="5.5.5 x64",
            lang_code="en",
            system_lang_code="en-US",
        )

    @classmethod
    def default_ios(cls) -> "DeviceFingerprint":
        """Дефолтный iOS fingerprint."""
        return cls(
            device_model="iPhone 14 Pro",
            system_version="iOS 17.4",
            app_version="10.14.5 (28538)",
            lang_code="en",
            system_lang_code="en-US",
        )


@dataclass
class SessionFileData:
    """Данные из .session файла SQLite."""

    user_id: Optional[int] = None
    dc_id: Optional[int] = None
    auth_key: Optional[bytes] = None
    phone: Optional[str] = None  # Номер телефона если найден

    def is_valid(self) -> bool:
        return self.user_id is not None and self.user_id > 0


def read_session_file(session_path: str) -> Optional[SessionFileData]:
    """
    Прочитать данные из .session файла (SQLite).

    Telethon хранит в SQLite:
    - sessions: dc_id, server_address, port, auth_key (256 байт)
    - entities: id, hash, username, phone, name, date
      - Строка с id=0 содержит user_id в поле hash

    Returns:
        SessionFileData или None при ошибке
    """
    try:
        conn = sqlite3.connect(session_path)
        cursor = conn.cursor()

        result = SessionFileData()

        # Получаем dc_id и auth_key из sessions
        try:
            cursor.execute("SELECT dc_id, auth_key FROM sessions LIMIT 1")
            row = cursor.fetchone()
            if row:
                result.dc_id = row[0]
                result.auth_key = row[1]
        except sqlite3.OperationalError:
            pass

        # Получаем user_id из entities где id=0 (специальная строка)
        # В Telethon: строка с id=0 хранит user_id в поле hash
        try:
            cursor.execute("SELECT hash FROM entities WHERE id = 0")
            row = cursor.fetchone()
            if row and row[0]:
                result.user_id = row[0]
                logger.debug(f"Found user_id={result.user_id} in entities (id=0)")
        except sqlite3.OperationalError:
            pass

        # ВАЖНО:
        # Не пытаемся "угадывать" user_id по первой сущности.
        # В entities лежат и чаты/каналы/контакты, и выбор "первого" ID часто даёт неверный tg_user_id.
        # Если user_id не найден через id=0, лучше оставить None и получить его через connect() один раз.

        # Пробуем получить phone из entities (если есть user_id)
        if result.user_id and not result.phone:
            try:
                cursor.execute(
                    "SELECT phone FROM entities WHERE id = ?", (result.user_id,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    result.phone = str(row[0])
                    logger.debug(f"Found phone={result.phone} in entities")
            except sqlite3.OperationalError:
                pass

        conn.close()

        # Fallback 2: извлекаем phone из имени файла (user_id из имени НЕ используем)
        filename = os.path.basename(session_path).replace(".session", "")
        # Убираем суффиксы типа _telethon, _pyrogram
        for suffix in ["_telethon", "_pyrogram", "_tdata", "_session"]:
            filename = filename.replace(suffix, "")

        # Пробуем распарсить как число
        try:
            # Убираем + в начале для телефонов
            clean_name = filename.lstrip("+")
            parsed_id = int(clean_name)

            # Различаем user_id и телефон:
            # - User_id: обычно 6-10 цифр
            # - Телефон: обычно 10-15 цифр
            num_digits = len(clean_name)

            # Телефон: обычно 10-15 цифр. Для 9-10 цифр слишком много пересечений с user_id,
            # поэтому здесь сохраняем только phone, а user_id получаем через connect().
            if num_digits >= 10:
                if not result.phone:
                    result.phone = clean_name
                    logger.info(f"Extracted phone={result.phone} from filename")
        except ValueError:
            pass

        if result.auth_key and len(result.auth_key) == 256:
            logger.debug(
                f"Session file {session_path}: dc_id={result.dc_id}, user_id={result.user_id}"
            )
            return result
        else:
            logger.warning(f"Invalid auth_key in session {session_path}")
            return None

    except Exception as e:
        logger.error(f"Failed to read session file {session_path}: {e}")
        return None


def extract_fingerprint_from_dict(data: dict) -> Optional[DeviceFingerprint]:
    """
    Извлечь device fingerprint из JSON словаря.

    Поддерживаемые форматы:
    1) {"device": "...", "sdk": "...", "app_version": "..."}  # TelegramExpert
    2) {"device_model": "...", "system_version": "..."}  # Стандартный
    3) {"system": {"device": "...", "version": "..."}}  # Вложенный

    Returns:
        DeviceFingerprint или None если не найдено
    """
    if not isinstance(data, dict):
        return None

    fp = DeviceFingerprint()

    # Варианты ключей для device_model
    device_keys = ["device", "device_model", "deviceModel", "model", "device_name"]
    for key in device_keys:
        if key in data and data[key]:
            fp.device_model = str(data[key])
            break

    # Варианты ключей для system_version (sdk в TelegramExpert)
    system_keys = [
        "sdk",
        "system_version",
        "systemVersion",
        "os_version",
        "osVersion",
        "system",
    ]
    for key in system_keys:
        if key in data and data[key]:
            fp.system_version = str(data[key])
            break

    # Варианты ключей для app_version
    app_keys = ["app_version", "appVersion", "version", "client_version"]
    for key in app_keys:
        if key in data and data[key]:
            fp.app_version = str(data[key])
            break

    # lang_code
    lang_keys = ["lang_code", "langCode", "language", "lang"]
    for key in lang_keys:
        if key in data and data[key]:
            fp.lang_code = str(data[key])
            break

    # system_lang_code
    sys_lang_keys = ["system_lang_code", "systemLangCode", "system_language"]
    for key in sys_lang_keys:
        if key in data and data[key]:
            fp.system_lang_code = str(data[key])
            break

    # Проверяем, нашли ли что-то
    if fp.is_valid():
        return fp

    # Ищем во вложенных объектах
    nested_keys = ["system", "device_info", "client", "app", "telegram"]
    for key in nested_keys:
        if key in data and isinstance(data[key], dict):
            nested_fp = extract_fingerprint_from_dict(data[key])
            if nested_fp and nested_fp.is_valid():
                return nested_fp

    return None


def extract_api_credentials_from_dict(data: dict) -> Optional[Tuple[int, str]]:
    """
    Извлечь api_id и api_hash из словаря с поддержкой разных структур.

    Поддерживаемые форматы:
    1) {"api_id": 123, "api_hash": "abcd..."}
    2) {"app_id": 123, "app_hash": "abcd..."}
    3) {"telegram_api_id": 123, "telegram_api_hash": "abcd..."}
    4) {"app": {"api_id": 123, "api_hash": "abcd..."}}
    5) {"telegram": {"api_id": 123, "api_hash": "abcd..."}}
    6) {"credentials": {"api_id": 123, "api_hash": "abcd..."}}
    7) {"config": {"api_id": 123, "api_hash": "abcd..."}}

    Returns:
        (api_id, api_hash) или None если не найдено
    """
    if not isinstance(data, dict):
        return None

    # Варианты ключей для api_id
    api_id_keys = [
        "api_id",
        "app_id",
        "telegram_api_id",
        "apiId",
        "appId",
        "API_ID",
        "APP_ID",
    ]
    # Варианты ключей для api_hash
    api_hash_keys = [
        "api_hash",
        "app_hash",
        "telegram_api_hash",
        "apiHash",
        "appHash",
        "API_HASH",
        "APP_HASH",
    ]

    def find_credentials(obj: dict) -> Optional[Tuple[int, str]]:
        """Поиск credentials в словаре."""
        api_id = None
        api_hash = None

        for key in api_id_keys:
            if key in obj and obj[key]:
                try:
                    api_id = int(obj[key])
                    break
                except (ValueError, TypeError):
                    continue

        for key in api_hash_keys:
            if key in obj and obj[key]:
                api_hash = str(obj[key])
                break

        if api_id and api_hash:
            return (api_id, api_hash)
        return None

    # 1. Сначала пробуем на верхнем уровне
    result = find_credentials(data)
    if result:
        return result

    # 2. Ищем во вложенных объектах
    nested_keys = [
        "app",
        "telegram",
        "credentials",
        "config",
        "api",
        "settings",
        "tg",
        "account",
    ]
    for key in nested_keys:
        if key in data and isinstance(data[key], dict):
            result = find_credentials(data[key])
            if result:
                return result

    # 3. Рекурсивный поиск в любых вложенных объектах (на 1 уровень)
    for key, value in data.items():
        if isinstance(value, dict):
            result = find_credentials(value)
            if result:
                return result

    return None


def extract_phone_from_dict(data: dict) -> Optional[str]:
    """
    Извлечь номер телефона из JSON словаря.

    Поддерживаемые ключи: phone, phone_number, number, phoneNumber
    """
    if not isinstance(data, dict):
        return None

    phone_keys = [
        "phone",
        "phone_number",
        "number",
        "phoneNumber",
        "Phone",
        "tel",
        "mobile",
    ]

    def find_phone(obj: dict) -> Optional[str]:
        for key in phone_keys:
            if key in obj and obj[key]:
                phone = str(obj[key]).lstrip("+").replace(" ", "").replace("-", "")
                if phone.isdigit() and len(phone) >= 10:
                    return phone
        return None

    # На верхнем уровне
    result = find_phone(data)
    if result:
        return result

    # Во вложенных объектах
    for key, value in data.items():
        if isinstance(value, dict):
            result = find_phone(value)
            if result:
                return result

    return None


def extract_phone_from_json(path: str) -> Optional[str]:
    """Извлечь номер телефона из JSON файла."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return extract_phone_from_dict(data)
    except Exception:
        return None


def extract_api_credentials(path: str) -> Optional[Tuple[int, str]]:
    """
    Извлечь api_id и api_hash из JSON файла.

    Args:
        path: Путь к JSON файлу

    Returns:
        (api_id, api_hash) или None если не найдено
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return extract_api_credentials_from_dict(data)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to read {path}: {e}")
        return None


def find_api_json(directory: str) -> Optional[ApiCredentials]:
    """
    Найти и прочитать JSON файл с api_id/api_hash в директории или её родительских папках.

    Стратегия поиска:
    1. Сначала ищет файлы из ACCOUNT_JSON_FILENAMES (api.json, config.json, etc.)
    2. Затем ищет любой .json файл в директории
    3. Поднимается на 3 уровня вверх по директориям

    Returns:
        ApiCredentials или None если не найден
    """
    search_names = settings.account_json_filenames_list

    # Поиск в текущей директории и родительских (до 3 уровней)
    current_dir = directory
    for depth in range(4):  # 0, 1, 2, 3 — текущая + 3 уровня вверх
        if not os.path.isdir(current_dir):
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent
            continue

        # 1. Сначала ищем приоритетные файлы
        for name in search_names:
            json_path = os.path.join(current_dir, name)
            if os.path.exists(json_path):
                result = extract_api_credentials(json_path)
                if result:
                    api_id, api_hash = result
                    logger.info(
                        f"Found API credentials in {json_path}: api_id={api_id}"
                    )
                    return ApiCredentials(
                        api_id=api_id,
                        api_hash=api_hash,
                        source="json",
                        json_path=json_path,
                    )
                else:
                    logger.warning(
                        f"JSON found but no valid api_id/api_hash: {json_path}"
                    )

        # 2. Ищем любой .json файл
        if depth == 0:  # Только в текущей директории
            try:
                for filename in os.listdir(current_dir):
                    if (
                        filename.lower().endswith(".json")
                        and filename not in search_names
                    ):
                        json_path = os.path.join(current_dir, filename)
                        if os.path.isfile(json_path):
                            result = extract_api_credentials(json_path)
                            if result:
                                api_id, api_hash = result
                                logger.info(
                                    f"Found API credentials in {json_path}: api_id={api_id}"
                                )
                                return ApiCredentials(
                                    api_id=api_id,
                                    api_hash=api_hash,
                                    source="json",
                                    json_path=json_path,
                                )
            except OSError:
                pass

        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent

    return None


def get_api_credentials(
    directory: Optional[str] = None, require_json: bool = False
) -> Tuple[Optional[int], Optional[str], str]:
    """
    Получить API credentials: сначала из JSON файла, иначе из настроек (если разрешён fallback).

    Args:
        directory: Директория для поиска JSON
        require_json: Если True и JSON не найден — вернёт (None, None, error)

    Returns:
        (api_id, api_hash, source) где source = "json" | "env" | "error:..."
    """
    if directory:
        creds = find_api_json(directory)
        if creds:
            return creds.api_id, creds.api_hash, "json"

    # JSON не найден
    if not settings.fallback_env_api:
        # Fallback отключён — ошибка
        return None, None, "error:JSON с api_id/api_hash не найден"

    # Fallback на .env.example
    if settings.api_id and settings.api_hash:
        return settings.api_id, settings.api_hash, "env"

    return None, None, "error:API credentials не найдены (ни в JSON, ни в .env.example)"


@dataclass
class SessionValidationResult:
    """Результат валидации сессии."""

    success: bool
    tg_user_id: Optional[int] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    is_premium: Optional[bool] = None
    error: Optional[str] = None
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    api_source: Optional[str] = None  # "json" | "env"
    # Fingerprint
    fingerprint: Optional[DeviceFingerprint] = None


def find_json_in_directory(directory: str) -> Optional[str]:
    """
    Найти первый JSON файл в директории.

    Returns:
        Путь к JSON файлу или None
    """
    search_names = settings.account_json_filenames_list

    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)

    if not os.path.isdir(directory):
        return None

    # 1. Приоритетные файлы
    for name in search_names:
        json_path = os.path.join(directory, name)
        if os.path.exists(json_path):
            return json_path

    # 2. Любой .json
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith(".json"):
                return os.path.join(directory, filename)
    except OSError:
        pass

    return None


def get_fingerprint_from_json(json_path: str) -> Optional[DeviceFingerprint]:
    """
    Извлечь fingerprint из JSON файла.

    Args:
        json_path: Путь к JSON файлу

    Returns:
        DeviceFingerprint или None
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return extract_fingerprint_from_dict(data)
    except Exception as e:
        logger.debug(f"Failed to extract fingerprint from {json_path}: {e}")
        return None


def get_fingerprint_for_session(session_path: str) -> DeviceFingerprint:
    """
    Получить fingerprint для сессии.

    Стратегия:
    1. Сначала ищет JSON с тем же именем что и сессия (phone.json)
    2. Если не найден — ищет общий JSON в директории
    3. Если не найден — возвращает дефолтный Android fingerprint

    ⚠️ ВАЖНО: Fingerprint используется КАК ЕСТЬ, без изменений!
    Telegram отслеживает device fingerprint - любое изменение убьёт сессию.

    Args:
        session_path: Путь к .session файлу

    Returns:
        DeviceFingerprint (всегда возвращает значение)
    """
    session_dir = os.path.dirname(session_path)
    session_basename = os.path.basename(session_path)
    session_name = session_basename.replace(".session", "")

    # Убираем суффиксы для альтернативного поиска
    clean_name = session_name
    for suffix in ["_telethon", "_pyrogram", "_tdata", "_session"]:
        clean_name = clean_name.replace(suffix, "")

    fp = None
    source = "default"

    # 1. Ищем JSON с точным именем сессии
    matching_json = os.path.join(session_dir, f"{session_name}.json")
    if os.path.exists(matching_json):
        fp = get_fingerprint_from_json(matching_json)
        if fp and fp.is_valid():
            source = matching_json

    # 2. Ищем JSON без суффиксов (205318444.json для 205318444_telethon.session)
    if not fp and clean_name != session_name:
        clean_json = os.path.join(session_dir, f"{clean_name}.json")
        if os.path.exists(clean_json):
            fp = get_fingerprint_from_json(clean_json)
            if fp and fp.is_valid():
                source = clean_json

    # 3. Fallback: ищем любой JSON в директории
    if not fp:
        json_path = find_json_in_directory(session_dir)
        if json_path:
            fp = get_fingerprint_from_json(json_path)
            if fp and fp.is_valid():
                source = json_path

    # 4. Дефолт если ничего не найдено
    if not fp:
        fp = DeviceFingerprint.default_android()
        source = "default"

    # Логируем fingerprint КАК ЕСТЬ (без изменений!)
    logger.info(
        f"Fingerprint from {source}: device='{fp.device_model}', system='{fp.system_version}'"
    )

    return fp


def get_phone_for_session(session_path: str) -> Optional[str]:
    """
    Получить номер телефона для сессии.

    Источники (по приоритету):
    1. JSON с тем же именем что и сессия
    2. JSON с именем без суффиксов (_telethon и т.д.)
    3. Имя файла сессии (если выглядит как телефон)
    4. Любой JSON в директории

    Returns:
        Номер телефона или None
    """
    session_dir = os.path.dirname(session_path)
    session_basename = os.path.basename(session_path)
    session_name = session_basename.replace(".session", "")

    # Убираем суффиксы
    clean_name = session_name
    for suffix in ["_telethon", "_pyrogram", "_tdata", "_session"]:
        clean_name = clean_name.replace(suffix, "")
    clean_name_digits = clean_name.lstrip("+")

    # 1. JSON с точным именем сессии
    matching_json = os.path.join(session_dir, f"{session_name}.json")
    if os.path.exists(matching_json):
        phone = extract_phone_from_json(matching_json)
        if phone:
            logger.info(f"Found phone in {matching_json}: {phone}")
            return phone

    # 2. JSON с именем без суффиксов (205318444.json для 205318444_telethon.session)
    if clean_name != session_name:
        clean_json = os.path.join(session_dir, f"{clean_name}.json")
        if os.path.exists(clean_json):
            phone = extract_phone_from_json(clean_json)
            if phone:
                logger.info(f"Found phone in {clean_json}: {phone}")
                return phone

    # 3. Имя файла как телефон (если 10+ цифр)
    if clean_name_digits.isdigit() and len(clean_name_digits) >= 10:
        logger.info(f"Using filename as phone: {clean_name_digits}")
        return clean_name_digits

    # 4. Любой JSON в директории
    json_path = find_json_in_directory(session_dir)
    if json_path:
        phone = extract_phone_from_json(json_path)
        if phone:
            logger.info(f"Found phone in {json_path}: {phone}")
            return phone

    return None


def ensure_directories() -> None:
    """Создать необходимые директории."""
    for dir_path in [INBOX_DIR, SESSIONS_DIR, TDATA_DIR]:
        os.makedirs(dir_path, exist_ok=True)


async def validate_session(
    session_path: str,
    timeout: int = 30,
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    skip_connect: bool = False,
) -> SessionValidationResult:
    """
    Валидация .session файла через Telethon.

    ВАЖНО: Эта функция подключается к Telegram БЕЗ прокси!
    Используйте skip_connect=True для проверки только файлов без подключения.

    Args:
        session_path: Путь к .session файлу
        timeout: Таймаут подключения в секундах
        api_id: API ID (если None - ищет в JSON или .env.example)
        api_hash: API Hash (если None - ищет в JSON или .env.example)
        skip_connect: Если True — только проверяет файлы, не подключается к Telegram

    Returns:
        SessionValidationResult с данными аккаунта или ошибкой.
    """
    # Определяем API credentials
    session_dir = os.path.dirname(session_path)
    api_source = "provided"

    if api_id is None or api_hash is None:
        found_api_id, found_api_hash, source = get_api_credentials(session_dir)

        # Проверяем на ошибку
        if source.startswith("error:"):
            error_msg = source.replace("error:", "")
            return SessionValidationResult(success=False, error=error_msg)

        api_id = api_id or found_api_id
        api_hash = api_hash or found_api_hash
        api_source = source

    # Получаем fingerprint
    fingerprint = get_fingerprint_for_session(session_path)

    # Получаем phone из JSON или имени файла
    phone_from_json = get_phone_for_session(session_path)

    # Если skip_connect — читаем данные из SQLite файла без подключения к Telegram
    if skip_connect:
        logger.info(f"Skipping connection for session: {session_path}")

        # Читаем user_id напрямую из .session файла (SQLite)
        session_data = read_session_file(session_path)

        # Определяем phone: из JSON > из SQLite > из имени файла
        final_phone = phone_from_json or (session_data.phone if session_data else None)

        if session_data and session_data.is_valid():
            logger.info(
                f"Read from session file: user_id={session_data.user_id}, phone={final_phone}"
            )
            return SessionValidationResult(
                success=True,
                tg_user_id=session_data.user_id,
                phone=final_phone,
                api_id=api_id,
                api_hash=api_hash,
                api_source=api_source,
                fingerprint=fingerprint,
            )
        elif session_data:
            # auth_key есть, но user_id не найден — всё равно валидная сессия
            logger.info(f"Session valid, user_id pending, phone={final_phone}")
            return SessionValidationResult(
                success=True,
                phone=final_phone,
                api_id=api_id,
                api_hash=api_hash,
                api_source=api_source,
                fingerprint=fingerprint,
            )
        else:
            return SessionValidationResult(
                success=False,
                error="Invalid or corrupted session file",
                fingerprint=fingerprint,
            )

    client = None
    try:
        logger.info(
            f"Validating session: {session_path} with api_id={api_id} (source={api_source})"
        )

        # Создаём клиент С FINGERPRINT
        client = TelegramClient(
            session_path.replace(".session", ""),  # Telethon сам добавит .session
            api_id,
            api_hash,
            device_model=fingerprint.device_model,
            system_version=fingerprint.system_version,
            app_version=fingerprint.app_version,
            lang_code=fingerprint.lang_code or "en",
            system_lang_code=fingerprint.system_lang_code or "en-us",
            connection_retries=2,
            retry_delay=1,
        )

        # Подключение с таймаутом
        try:
            await asyncio.wait_for(client.connect(), timeout=timeout)
        except asyncio.TimeoutError:
            return SessionValidationResult(
                success=False,
                error=f"Connection timeout ({timeout}s)",
                fingerprint=fingerprint,
            )

        # Проверка авторизации с таймаутом
        try:
            is_authorized = await asyncio.wait_for(
                client.is_user_authorized(), timeout=10
            )
        except asyncio.TimeoutError:
            return SessionValidationResult(
                success=False,
                error="Authorization check timeout",
                fingerprint=fingerprint,
            )

        if not is_authorized:
            return SessionValidationResult(
                success=False,
                error="Session not authorized (expired or invalid)",
                fingerprint=fingerprint,
            )

        # Получение информации с таймаутом
        try:
            me = await asyncio.wait_for(client.get_me(), timeout=10)
        except asyncio.TimeoutError:
            return SessionValidationResult(
                success=False, error="Get user info timeout", fingerprint=fingerprint
            )

        if not me:
            return SessionValidationResult(
                success=False, error="Could not get user info", fingerprint=fingerprint
            )

        # Определяем premium статус (совместимо с v1 и v2)
        is_premium = get_user_premium(me)

        return SessionValidationResult(
            success=True,
            tg_user_id=me.id,
            username=me.username,
            phone=me.phone,
            is_premium=is_premium,
            api_id=api_id,
            api_hash=api_hash,
            api_source=api_source,
            fingerprint=fingerprint,
        )

    except AuthKeyUnregisteredError:
        return SessionValidationResult(
            success=False,
            error="Auth key unregistered (session revoked)",
            fingerprint=fingerprint,
        )

    except SessionPasswordNeededError:
        return SessionValidationResult(
            success=False, error="2FA password required", fingerprint=fingerprint
        )

    except Exception as e:
        logger.exception(f"Session validation error: {e}")
        return SessionValidationResult(
            success=False, error=str(e), fingerprint=fingerprint
        )

    finally:
        if client:
            await client.disconnect()


async def check_duplicate(session: AsyncSession, tg_user_id: int) -> Optional[Account]:
    """Проверить, существует ли аккаунт с таким tg_user_id."""
    stmt = select(Account).where(Account.tg_user_id == tg_user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def import_session_file(
    session: AsyncSession, file_data: bytes, original_filename: str
) -> Tuple[bool, str, Optional[Account]]:
    """
    Импорт .session файла.

    Args:
        session: SQLAlchemy async session
        file_data: Содержимое файла
        original_filename: Оригинальное имя файла

    Returns:
        (success, message, account)
    """
    ensure_directories()

    # Проверка размера
    if len(file_data) > MAX_FILE_SIZE:
        return (
            False,
            f"Файл слишком большой (макс. {MAX_FILE_SIZE // 1024 // 1024} MB)",
            None,
        )

    # Проверка расширения
    if not original_filename.lower().endswith(".session"):
        return False, "Файл должен иметь расширение .session", None

    # Сохраняем во временную папку
    temp_id = str(uuid.uuid4())
    temp_path = os.path.join(INBOX_DIR, f"{temp_id}.session")

    try:
        with open(temp_path, "wb") as f:
            f.write(file_data)

        logger.info(f"Session saved to inbox: {temp_path}")

        # Валидируем сессию.
        # Сначала делаем лёгкую проверку без connect(), но если user_id не удалось извлечь из файла —
        # делаем ОДНО подключение, иначе начнут плодиться записи с tg_user_id=NULL.
        validation = await validate_session(temp_path, skip_connect=True)

        if not validation.success:
            # Не создаём запись с tg_user_id=NULL (иначе можно загрузить один и тот же аккаунт дважды).
            # Просто отклоняем импорт и чистим временный файл.
            try:
                os.remove(temp_path)
            except Exception:
                pass
            logger.warning(f"Session validation failed: {validation.error}")
            return False, f"Сессия невалидна: {validation.error}", None

        if validation.tg_user_id is None:
            logger.info(
                "tg_user_id not found in .session by file read; validating via connect() once"
            )
            validation2 = await validate_session(temp_path, skip_connect=False)
            if not validation2.success or validation2.tg_user_id is None:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                err = (
                    validation2.error
                    if validation2 and validation2.error
                    else "Не удалось определить TG User ID"
                )
                return (
                    False,
                    f"Сессия валидна, но не удалось определить аккаунт: {err}",
                    None,
                )
            validation = validation2

        # Перемещаем в постоянное хранилище (путь всегда одинаковый)
        final_dir = os.path.join(SESSIONS_DIR, str(validation.tg_user_id))
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, "account.session")

        # Проверка дубликата: вместо отказа — обновляем существующий аккаунт
        existing = await check_duplicate(session, validation.tg_user_id)

        # Если в БД уже накопились записи с tg_user_id=NULL (старое поведение),
        # попробуем аккуратно "склеить" по телефону.
        if not existing and validation.phone:
            stmt = (
                select(Account)
                .where(
                    Account.tg_user_id.is_(None),
                    Account.phone == validation.phone,
                )
                .order_by(Account.id.asc())
                .limit(1)
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                existing.tg_user_id = validation.tg_user_id
        if existing:
            # Заменяем session-файл
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
            except Exception:
                pass
            shutil.move(temp_path, final_path)

            # Обновляем запись
            existing.session_path = final_path
            existing.storage_type = StorageType.TELETHON_SESSION
            existing.username = validation.username or existing.username
            existing.phone = validation.phone or existing.phone
            existing.is_premium = (
                validation.is_premium
                if validation.is_premium is not None
                else existing.is_premium
            )

            # Сохраняем api_id/api_hash только если они отличаются от глобальных настроек
            existing.api_id = (
                validation.api_id if validation.api_id != settings.api_id else None
            )
            existing.api_hash = (
                validation.api_hash
                if validation.api_hash != settings.api_hash
                else None
            )

            # Fingerprint
            fp = validation.fingerprint
            if fp:
                existing.device_model = fp.device_model
                existing.system_version = fp.system_version
                existing.app_version = fp.app_version
                existing.lang_code = fp.lang_code
                existing.system_lang_code = fp.system_lang_code

            existing.error_text = None
            await session.flush()
            await session.refresh(existing)

            logger.info(
                f"Account merged (session updated): id={existing.id}, tg_user_id={existing.tg_user_id}"
            )
            return True, f"✅ Аккаунт обновлён (ID: {existing.id})", existing

        # Перемещаем session-файл (новый аккаунт)

        final_dir = os.path.join(SESSIONS_DIR, str(validation.tg_user_id))
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, "account.session")

        shutil.move(temp_path, final_path)
        logger.info(f"Session moved to: {final_path}")

        # Создаём запись в БД
        # Сохраняем api_id/api_hash только если они отличаются от глобальных настроек
        save_api_id = (
            validation.api_id if validation.api_id != settings.api_id else None
        )
        save_api_hash = (
            validation.api_hash if validation.api_hash != settings.api_hash else None
        )

        # Сохраняем fingerprint
        fp = validation.fingerprint

        account = Account(
            tg_user_id=validation.tg_user_id,
            username=validation.username,
            phone=validation.phone,
            storage_type=StorageType.TELETHON_SESSION,
            session_path=final_path,
            status=AccountStatus.FREE,
            is_premium=validation.is_premium,
            api_id=save_api_id,
            api_hash=save_api_hash,
            # Fingerprint fields
            device_model=fp.device_model if fp else None,
            system_version=fp.system_version if fp else None,
            app_version=fp.app_version if fp else None,
            lang_code=fp.lang_code if fp else None,
            system_lang_code=fp.system_lang_code if fp else None,
            error_text=None,
        )
        session.add(account)
        await session.flush()
        await session.refresh(account)

        logger.info(
            f"Account created: id={account.id}, tg_user_id={validation.tg_user_id}, api_id={save_api_id or 'default'}"
        )

        # Автоматически назначаем прокси по стране аккаунта
        proxy_info = ""
        assigned_proxy = await proxy_service.assign_proxy_to_account(
            session, account.id
        )
        if assigned_proxy:
            country_flag = proxy_service.get_country_flag(assigned_proxy.country)
            proxy_info = f"\n🌐 Прокси: {country_flag} `{assigned_proxy.host}:{assigned_proxy.port}`"
            logger.info(
                f"Auto-assigned proxy {assigned_proxy.id} ({assigned_proxy.country}) to account {account.id}"
            )

        # Формируем строку API источника
        api_source_str = (
            "📦 JSON" if validation.api_source == "json" else "⚙️ .env.example"
        )
        api_display = f"{validation.api_id}"[:8] + "..." if validation.api_id else "—"

        premium_mark = "⭐" if validation.is_premium else ""
        return (
            True,
            (
                f"✅ Аккаунт добавлен!\n\n"
                f"📱 ID: {account.id}\n"
                f"🆔 TG User ID: {validation.tg_user_id}\n"
                f"👤 Username: @{validation.username or 'нет'}\n"
                f"📞 Phone: {validation.phone or 'скрыт'}"
                f"{proxy_info}\n"
                f"🔑 API ID: `{api_display}` ({api_source_str})\n"
                f"{premium_mark} Premium: {'Да' if validation.is_premium else 'Нет'}"
            ),
            account,
        )

    except Exception as e:
        logger.exception(f"Import session error: {e}")
        # Очистка временного файла при ошибке
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, f"Ошибка импорта: {e}", None


# ============================================================
# Self-test функция для extract_api_credentials_from_dict
# ============================================================


def _self_test_extract_api_credentials():
    """
    Self-test для функции extract_api_credentials_from_dict.

    Запускается при импорте модуля в debug режиме или вручную.
    """
    test_cases = [
        # Формат 1: Простой плоский JSON
        ({"api_id": 12345, "api_hash": "abcdef123456"}, (12345, "abcdef123456")),
        # Формат 2: Альтернативные ключи app_id/app_hash
        ({"app_id": 67890, "app_hash": "xyz789"}, (67890, "xyz789")),
        # Формат 3: telegram_api_id / telegram_api_hash
        ({"telegram_api_id": 11111, "telegram_api_hash": "tghash"}, (11111, "tghash")),
        # Формат 4: Вложенный в "app"
        ({"app": {"api_id": 22222, "api_hash": "apphash"}}, (22222, "apphash")),
        # Формат 5: Вложенный в "telegram"
        ({"telegram": {"api_id": 33333, "api_hash": "tghash2"}}, (33333, "tghash2")),
        # Формат 6: Вложенный в "credentials"
        (
            {"credentials": {"app_id": 44444, "app_hash": "credhash"}},
            (44444, "credhash"),
        ),
        # Формат 7: Вложенный в "config"
        ({"config": {"api_id": 55555, "api_hash": "confhash"}}, (55555, "confhash")),
        # Формат 8: camelCase ключи
        ({"apiId": 66666, "apiHash": "camelhash"}, (66666, "camelhash")),
        # Формат 9: api_id как строка
        ({"api_id": "77777", "api_hash": "strhash"}, (77777, "strhash")),
        # Формат 10: Смешанные ключи
        ({"api_id": 88888, "app_hash": "mixhash"}, (88888, "mixhash")),
        # Формат 11: Произвольный вложенный объект
        (
            {"some_random_key": {"api_id": 99999, "api_hash": "randomhash"}},
            (99999, "randomhash"),
        ),
        # Негативные тесты
        ({"wrong_key": 123}, None),
        ({"api_id": 123}, None),  # Нет api_hash
        ({"api_hash": "hash"}, None),  # Нет api_id
        ({}, None),
        ({"api_id": None, "api_hash": "hash"}, None),
        ({"api_id": "", "api_hash": "hash"}, None),
    ]

    passed = 0
    failed = 0

    for data, expected in test_cases:
        result = extract_api_credentials_from_dict(data)
        if result == expected:
            passed += 1
        else:
            failed += 1
            logger.error(
                f"FAILED: extract_api_credentials_from_dict({data}) = {result}, expected {expected}"
            )

    logger.info(f"extract_api_credentials self-test: {passed} passed, {failed} failed")
    return failed == 0


# Запускаем self-test при импорте в debug режиме
if settings.debug:
    _self_test_extract_api_credentials()
