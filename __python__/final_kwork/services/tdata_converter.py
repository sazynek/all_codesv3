"""
Конвертер tdata (Telegram Desktop) в Telethon session.

Поддерживает:
- Старый формат с папками D877F783* и файлами DC*
- Современный формат с key_datas (расшифровка через local key)
"""

import asyncio
import hashlib
import logging
import os
import shutil
import sqlite3
import struct
import uuid
import zipfile
from typing import Optional, Tuple, List
from io import BytesIO
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Account, AccountStatus, StorageType
from services.session_import_service import (
    INBOX_DIR,
    TDATA_DIR,
    SESSIONS_DIR,
    MAX_FILE_SIZE,
    ensure_directories,
    validate_session,
    check_duplicate,
    get_api_credentials,
    find_api_json,
)
from services import proxy_service
from config import settings

# opentele несовместим с Python 3.13
OPENTELE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Поддерживаемые форматы архивов
SUPPORTED_ARCHIVES = (".zip",)


def _find_tdata_folder(extract_dir: str) -> Optional[str]:
    """Найти папку tdata в распакованном архиве."""
    # Ищем папку tdata внутри
    for root, dirs, files in os.walk(extract_dir):
        if "tdata" in dirs:
            return os.path.join(root, "tdata")
        # Если сама папка называется tdata
        if os.path.basename(root) == "tdata":
            all_items = dirs + files
            if any(
                f.startswith("D877F783") or f.startswith("key_") or f == "key_datas"
                for f in all_items
            ):
                return root

    # Проверяем, может сам extract_dir содержит содержимое tdata
    items = os.listdir(extract_dir) if os.path.exists(extract_dir) else []
    if any(
        f.startswith("D877F783") or f.startswith("key_") or f == "key_datas"
        for f in items
    ):
        return extract_dir

    return None


# ============================================================
# TDesktop AES-IGE расшифровка (правильная реализация)
# ============================================================


def _create_local_key_tdesktop(salt: bytes, passcode: bytes = b"") -> bytes:
    """
    TDesktop CreateLocalKey - правильная реализация.
    hashKey = SHA512(salt + passcode + salt), затем PBKDF2.
    """
    hash_key = hashlib.sha512()
    hash_key.update(salt)
    hash_key.update(passcode)
    hash_key.update(salt)

    iterations = 1 if not passcode else 100000
    return hashlib.pbkdf2_hmac("sha512", hash_key.digest(), salt, iterations, 256)


def _prepare_aes_oldmtp(
    key: bytes, msg_key: bytes, send: bool = False
) -> Tuple[bytes, bytes]:
    """
    TDesktop prepareAES_oldmtp - подготовка ключа и IV для AES-IGE.
    """
    x = 0 if send else 8

    sha1_a = hashlib.sha1(msg_key[:16] + key[x : x + 32]).digest()
    sha1_b = hashlib.sha1(
        key[x + 32 : x + 48] + msg_key[:16] + key[x + 48 : x + 64]
    ).digest()
    sha1_c = hashlib.sha1(key[x + 64 : x + 96] + msg_key[:16]).digest()
    sha1_d = hashlib.sha1(msg_key[:16] + key[x + 96 : x + 128]).digest()

    aes_key = sha1_a[:8] + sha1_b[8:20] + sha1_c[4:16]
    aes_iv = sha1_a[8:20] + sha1_b[:8] + sha1_c[16:20] + sha1_d[:8]

    return aes_key, aes_iv


def _aes_ige_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Расшифровка AES-256-IGE.
    """
    if len(data) % 16 != 0:
        raise ValueError("Data length must be multiple of 16")

    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()

    result = b""
    iv1 = iv[:16]
    iv2 = iv[16:]

    for i in range(0, len(data), 16):
        block = data[i : i + 16]
        xored = bytes(a ^ b for a, b in zip(block, iv2))
        decrypted_block = decryptor.update(xored)
        plain = bytes(a ^ b for a, b in zip(decrypted_block, iv1))
        result += plain
        iv1 = block
        iv2 = plain

    return result


def _decrypt_local(encrypted_data: bytes, local_key: bytes) -> Optional[bytes]:
    """
    Расшифровывает данные с локальным ключом TDesktop.

    Формат:
    - 16 bytes: msg_key (SHA1[:16] от plaintext)
    - остальное: зашифрованные данные

    Returns:
        Расшифрованные данные БЕЗ первых 4 байт (длина)
    """
    if len(encrypted_data) <= 16:
        return None

    msg_key = encrypted_data[:16]
    enc_data = encrypted_data[16:]

    if len(enc_data) % 16 != 0:
        return None

    try:
        aes_key, aes_iv = _prepare_aes_oldmtp(local_key, msg_key, send=False)
        decrypted = _aes_ige_decrypt(enc_data, aes_key, aes_iv)

        # Проверяем контрольную сумму
        check_key = hashlib.sha1(decrypted).digest()[:16]
        if check_key != msg_key:
            return None

        # Первые 4 байта - длина данных (little-endian)
        data_len = struct.unpack("<I", decrypted[:4])[0]
        return decrypted[4 : 4 + data_len - 4]
    except Exception as e:
        logger.debug(f"Decryption failed: {e}")
        return None


def _read_key_datas(tdata_path: str) -> Optional[Tuple[bytes, bytes, bytes]]:
    """
    Читает и парсит файл key_datas.

    Формат key_datas:
    - TDF$ (4 bytes magic)
    - version (4 bytes)
    - QByteArray salt (4 bytes size BE + data)
    - QByteArray encrypted (4 bytes size BE + data)

    Returns:
        (salt, encrypted_data, passcode_key) или None
    """
    key_datas_path = os.path.join(tdata_path, "key_datas")

    if not os.path.exists(key_datas_path):
        return None

    try:
        with open(key_datas_path, "rb") as f:
            data = f.read()

        if len(data) < 16:
            return None

        # Проверяем magic TDF$
        if data[:4] != b"TDF$":
            logger.debug(f"Invalid magic in key_datas: {data[:4]}")
            return None

        # Skip header (8 bytes)
        offset = 8

        # Read salt (QByteArray: 4 bytes size BE + data)
        salt_size = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        salt = data[offset : offset + salt_size]
        offset += salt_size

        # Read encrypted data
        enc_size = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        encrypted = data[offset : offset + enc_size]

        # Create passcode key
        passcode_key = _create_local_key_tdesktop(salt, b"")

        return (salt, encrypted, passcode_key)

    except Exception as e:
        logger.debug(f"Error reading key_datas: {e}")
        return None


def _extract_local_key(tdata_path: str) -> Optional[bytes]:
    """
    Извлекает local_key из key_datas.

    Returns:
        local_key (256 bytes) или None
    """
    result = _read_key_datas(tdata_path)
    if not result:
        return None

    salt, encrypted, passcode_key = result

    # Decrypt to get local_key
    decrypted = _decrypt_local(encrypted, passcode_key)
    if not decrypted or len(decrypted) < 256:
        logger.debug("Failed to decrypt local_key from key_datas")
        return None

    local_key = decrypted[:256]
    logger.info(f"Extracted local_key: {len(local_key)} bytes")
    return local_key


def _find_account_file(tdata_path: str) -> Optional[str]:
    """
    Находит файл аккаунта (D877F783D5D3EF8Cs или подобный).
    """
    for item in os.listdir(tdata_path):
        # Файл аккаунта заканчивается на 's' и начинается с D877F783
        if (
            item.startswith("D877F783")
            and item.endswith("s")
            and not os.path.isdir(os.path.join(tdata_path, item))
        ):
            return os.path.join(tdata_path, item)
    return None


def _extract_auth_key_from_account(
    account_file: str, local_key: bytes
) -> Optional[Tuple[bytes, int, int]]:
    """
    Извлекает auth_key из файла аккаунта.

    Returns:
        (auth_key, dc_id, user_id) или None
    """
    try:
        with open(account_file, "rb") as f:
            data = f.read()

        if len(data) < 16 or data[:4] != b"TDF$":
            logger.debug(f"Invalid account file format")
            return None

        # Skip header
        offset = 8

        # Read encrypted QByteArray
        enc_size = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        encrypted = data[offset : offset + enc_size]

        # Decrypt with local_key
        decrypted = _decrypt_local(encrypted, local_key)
        if not decrypted:
            logger.debug("Failed to decrypt account file")
            return None

        # Parse MtpAuthorization
        pos = 0

        # Block ID (should be 75 = MtpAuthorization)
        block_id = struct.unpack(">I", decrypted[pos : pos + 4])[0]
        pos += 4

        if block_id != 75:
            logger.debug(f"Unexpected block ID: {block_id}")
            return None

        # QByteArray with serialized data
        qba_size = struct.unpack(">I", decrypted[pos : pos + 4])[0]
        pos += 4
        serialized = decrypted[pos : pos + qba_size]

        # Parse serialized MTP authorization (Qt big-endian)
        spos = 0

        # Tag (int64, should be -1)
        tag = struct.unpack(">q", serialized[spos : spos + 8])[0]
        spos += 8

        if tag != -1:
            logger.debug(f"Unexpected tag: {tag}")
            return None

        # User ID (int64)
        user_id = struct.unpack(">q", serialized[spos : spos + 8])[0]
        spos += 8

        # Main DC ID (int32)
        main_dc = struct.unpack(">i", serialized[spos : spos + 4])[0]
        spos += 4

        # Keys count (int32)
        keys_count = struct.unpack(">i", serialized[spos : spos + 4])[0]
        spos += 4

        if keys_count < 1:
            logger.debug(f"No keys in account")
            return None

        # Read first key (dcId + 256 bytes auth_key)
        dc_id = struct.unpack(">i", serialized[spos : spos + 4])[0]
        spos += 4
        auth_key = serialized[spos : spos + 256]

        logger.info(f"Extracted auth_key: DC={dc_id}, user_id={user_id}")
        return (auth_key, dc_id, user_id)

    except Exception as e:
        logger.exception(f"Error extracting auth_key: {e}")
        return None


def _find_account_folders(tdata_path: str) -> List[str]:
    """Находит папки аккаунтов в tdata."""
    accounts = []

    for item in os.listdir(tdata_path):
        item_path = os.path.join(tdata_path, item)
        if os.path.isdir(item_path) and item.startswith("D877F783"):
            accounts.append(item_path)

    return accounts


def _read_auth_key_from_key_datas(tdata_path: str) -> Optional[Tuple[bytes, int]]:
    """
    Читает auth_key из современного формата TDesktop с расшифровкой.

    Использует правильный алгоритм:
    1. Парсит key_datas (TDF$ формат)
    2. Создаёт passcode_key через SHA512(salt+passcode+salt) → PBKDF2
    3. Расшифровывает local_key
    4. Находит файл аккаунта (D877F783...s)
    5. Расшифровывает MtpAuthorization
    6. Извлекает auth_key

    Returns:
        (auth_key, dc_id) или None
    """
    logger.info(f"Decrypting tdata from: {tdata_path}")

    # 1. Извлекаем local_key из key_datas
    local_key = _extract_local_key(tdata_path)
    if not local_key:
        logger.warning("Could not extract local_key from key_datas")
        return None

    # 2. Находим файл аккаунта
    account_file = _find_account_file(tdata_path)
    if not account_file:
        logger.warning("Account file not found in tdata")
        return None

    logger.info(f"Found account file: {account_file}")

    # 3. Извлекаем auth_key
    result = _extract_auth_key_from_account(account_file, local_key)
    if not result:
        logger.warning("Could not extract auth_key from account file")
        return None

    auth_key, dc_id, user_id = result
    logger.info(f"Successfully extracted auth_key: DC={dc_id}, user_id={user_id}")

    return (auth_key, dc_id)


def _read_auth_key_from_folder(account_folder: str) -> Optional[Tuple[bytes, int]]:
    """
    Читает auth_key из папки аккаунта.

    Ищет файлы вида DC1, DC2 и т.д.

    Returns:
        (auth_key, dc_id) или None
    """
    logger.info(f"Searching auth_key in: {account_folder}")

    for f in os.listdir(account_folder):
        # Файлы DC1, DC2 и т.д. (без s на конце - это ключи)
        if f.startswith("DC") and len(f) <= 4 and not f.endswith("s"):
            dc_file = os.path.join(account_folder, f)
            try:
                with open(dc_file, "rb") as file:
                    data = file.read()
                    logger.debug(f"Reading {dc_file}, size: {len(data)}")

                    if len(data) >= 260:
                        # auth_key = 256 байт, первые 4 байта - заголовок/версия
                        auth_key = data[4:260]
                        dc_id = int(f[2:]) if f[2:].isdigit() else 2

                        logger.info(
                            f"Found auth_key in {f}, DC: {dc_id}, key_len: {len(auth_key)}"
                        )
                        return (auth_key, dc_id)
            except Exception as e:
                logger.debug(f"Error reading {dc_file}: {e}")

    return None


def _create_telethon_session(
    session_path: str, auth_key: bytes, dc_id: int = 2
) -> bool:
    """
    Создаёт файл сессии Telethon с заданным auth_key.

    Returns:
        True если успешно
    """
    try:
        conn = sqlite3.connect(session_path)
        c = conn.cursor()

        # Создаём таблицы как в Telethon
        c.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
            dc_id INTEGER PRIMARY KEY,
            server_address TEXT,
            port INTEGER,
            auth_key BLOB,
            takeout_id INTEGER
        )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY,
            hash INTEGER NOT NULL,
            username TEXT,
            phone TEXT,
            name TEXT,
            date INTEGER
        )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS sent_files (
            md5_digest BLOB,
            file_size INTEGER,
            type INTEGER,
            id INTEGER,
            hash INTEGER,
            PRIMARY KEY (md5_digest, file_size, type)
        )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS update_state (
            id INTEGER PRIMARY KEY,
            pts INTEGER,
            qts INTEGER,
            date INTEGER,
            seq INTEGER
        )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS version (
            version INTEGER PRIMARY KEY
        )"""
        )

        # DC серверы Telegram (production)
        dc_addresses = {
            1: ("149.154.175.53", 443),
            2: ("149.154.167.51", 443),
            3: ("149.154.175.100", 443),
            4: ("149.154.167.91", 443),
            5: ("91.108.56.130", 443),
        }

        addr, port = dc_addresses.get(dc_id, dc_addresses[2])

        # Вставляем сессию
        c.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?)",
            (dc_id, addr, port, auth_key, None),
        )

        c.execute("INSERT OR REPLACE INTO version VALUES (?)", (7,))

        conn.commit()
        conn.close()

        logger.info(f"Created Telethon session: {session_path}, DC: {dc_id}")
        return True

    except Exception as e:
        logger.exception(f"Failed to create session: {e}")
        return False


def _convert_with_opentele(
    tdata_path: str, output_session_path: str
) -> Tuple[bool, str]:
    """
    Конвертация через opentele (рекомендуемый способ).

    Returns:
        (success, message)
    """
    if not OPENTELE_AVAILABLE:
        return False, "opentele не установлен"

    try:
        logger.info(f"Converting with opentele: {tdata_path}")

        # Загружаем tdata
        tdesk = TDesktop(tdata_path)

        if not tdesk.isLoaded():
            return False, "opentele: не удалось загрузить tdata"

        # Проверяем наличие аккаунтов
        if not tdesk.accounts:
            return False, "opentele: аккаунты не найдены в tdata"

        # Берём первый аккаунт
        account = tdesk.accounts[0]

        logger.info(f"opentele: found account, converting to session...")

        # Конвертируем в Telethon session
        # Убираем .session если есть в пути
        session_name = output_session_path.replace(".session", "")

        # Получаем API credentials из JSON или настроек
        tdata_dir = os.path.dirname(tdata_path)
        api_id, api_hash = get_api_credentials(tdata_dir)

        # Синхронная конвертация
        client = account.ToTelethon(
            session=session_name, api_id=api_id, api_hash=api_hash
        )

        # Проверяем что файл создан
        if os.path.exists(output_session_path) or os.path.exists(
            session_name + ".session"
        ):
            logger.info(f"opentele: session created successfully")
            return True, "Конвертация через opentele успешна"
        else:
            return False, "opentele: session файл не создан"

    except Exception as e:
        logger.exception(f"opentele conversion error: {e}")
        return False, f"opentele error: {e}"


def _sync_convert_tdata(tdata_path: str, output_session_path: str) -> Tuple[bool, str]:
    """
    Синхронная конвертация tdata в session.

    Сначала пробует opentele, затем ручной парсинг.
    """
    logger.info(f"Converting tdata: {tdata_path}")

    # 1. Сначала пробуем opentele (самый надёжный способ)
    if OPENTELE_AVAILABLE:
        success, msg = _convert_with_opentele(tdata_path, output_session_path)
        if success:
            return True, msg
        logger.warning(f"opentele failed: {msg}, trying manual parsing...")

    # 2. Fallback: пробуем современный формат key_datas
    result = _read_auth_key_from_key_datas(tdata_path)
    if result:
        auth_key, dc_id = result
        if _create_telethon_session(output_session_path, auth_key, dc_id):
            return True, "Конвертация успешна (из key_datas)"

    # 3. Ищем папки аккаунтов
    account_folders = _find_account_folders(tdata_path)

    if not account_folders:
        logger.warning(f"No account folders (D877F783*) found in {tdata_path}")

        # Может быть в root есть файлы DC*?
        for f in os.listdir(tdata_path):
            if f.startswith("DC") and len(f) <= 4:
                # Пробуем как root-level аккаунт
                result = _read_auth_key_from_folder(tdata_path)
                if result:
                    auth_key, dc_id = result
                    if _create_telethon_session(output_session_path, auth_key, dc_id):
                        return True, "Конвертация успешна"

        return False, "Не найдены папки аккаунтов (D877F783*) или файлы DC*"

    # Берём первый аккаунт
    account_folder = account_folders[0]
    logger.info(f"Processing account folder: {account_folder}")

    # Читаем auth_key
    result = _read_auth_key_from_folder(account_folder)

    if not result:
        # Пробуем в подпапках (D877F783D5D3EF8C0 и т.д.)
        for subfolder in os.listdir(account_folder):
            subfolder_path = os.path.join(account_folder, subfolder)
            if os.path.isdir(subfolder_path):
                result = _read_auth_key_from_folder(subfolder_path)
                if result:
                    break

    if not result:
        return False, (
            "Не удалось извлечь auth_key из tdata.\n\n"
            "**Причина:** Современный TDesktop шифрует данные.\n\n"
            "**Решение:** Экспортируйте .session файл вручную:\n\n"
            "1. На ПК с Telegram Desktop выполните:\n"
            "```python\n"
            "from telethon.sync import TelegramClient\n"
            "from telethon.sessions import StringSession\n"
            "client = TelegramClient('tdata_session', API_ID, API_HASH)\n"
            "client.start()\n"
            "print(client.session.save())\n"
            "```\n\n"
            "2. Или используйте /add_session с готовым .session файлом"
        )

    auth_key, dc_id = result

    # Создаём session
    if _create_telethon_session(output_session_path, auth_key, dc_id):
        return True, "Конвертация успешна"

    return False, "Ошибка создания session файла"


async def convert_tdata_to_session(
    tdata_path: str, output_dir: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Асинхронная конвертация tdata в Telethon session.

    Args:
        tdata_path: Путь к папке tdata
        output_dir: Директория для сохранения session (если None - временная)

    Returns:
        (success, message, session_path)
    """
    ensure_directories()

    # Создаём временную директорию для session
    if not output_dir:
        output_dir = os.path.join(INBOX_DIR, f"conv_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)

    temp_session_path = os.path.join(output_dir, "converted.session")

    # Запускаем синхронную конвертацию в executor
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(
        None, _sync_convert_tdata, tdata_path, temp_session_path
    )

    if success and os.path.exists(temp_session_path):
        return True, message, temp_session_path

    # Очистка при неудаче
    if os.path.exists(output_dir) and output_dir.startswith(INBOX_DIR):
        shutil.rmtree(output_dir, ignore_errors=True)

    return False, message, None


async def import_tdata_archive(
    session: AsyncSession, file_data: bytes, original_filename: str
) -> Tuple[bool, str, Optional[Account]]:
    """
    Импорт tdata из архива с автоматической конвертацией.

    Args:
        session: SQLAlchemy async session
        file_data: Содержимое архива
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
    ext = os.path.splitext(original_filename.lower())[1]
    if ext not in SUPPORTED_ARCHIVES:
        return (
            False,
            f"Неподдерживаемый формат. Поддерживаются: {', '.join(SUPPORTED_ARCHIVES)}",
            None,
        )

    temp_id = str(uuid.uuid4())
    archive_path = os.path.join(INBOX_DIR, f"{temp_id}{ext}")
    extract_dir = os.path.join(TDATA_DIR, temp_id)

    try:
        # Сохраняем архив
        with open(archive_path, "wb") as f:
            f.write(file_data)

        logger.info(f"Archive saved: {archive_path}")

        # Распаковываем
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)

        # Ищем папку tdata
        tdata_path = _find_tdata_folder(extract_dir)

        if not tdata_path:
            shutil.rmtree(extract_dir, ignore_errors=True)
            os.remove(archive_path)
            return (
                False,
                (
                    "❌ В архиве не найдена папка tdata\n\n"
                    "Убедитесь, что архив содержит:\n"
                    "• Папку `tdata` с данными Telegram Desktop\n"
                    "• Или содержимое tdata (файлы D877F783*, key_datas и т.д.)"
                ),
                None,
            )

        logger.info(f"tdata found: {tdata_path}")

        # Удаляем архив
        os.remove(archive_path)

        # Пробуем конвертировать
        convert_success, convert_msg, session_path = await convert_tdata_to_session(
            tdata_path
        )

        if convert_success and session_path:
            # Валидируем полученную сессию.
            # Сначала без connect(), но если user_id не найден — делаем ОДНО подключение, чтобы не
            # создавать аккаунты с tg_user_id=NULL (они не дедуплицируются).
            validation = await validate_session(session_path, skip_connect=True)

            if validation.success and validation.tg_user_id is None:
                logger.info(
                    "tg_user_id not found in converted .session by file read; validating via connect() once"
                )
                validation2 = await validate_session(session_path, skip_connect=False)
                if validation2.success and validation2.tg_user_id is not None:
                    validation = validation2

            # Без tg_user_id нельзя ни дедуплицировать, ни правильно хранить/выдавать аккаунт.
            # Чтобы не плодить записи с tg_user_id=NULL, сохраняем как DISABLED.
            if validation.success and validation.tg_user_id is None:
                logger.warning(
                    "Converted session looks valid, but tg_user_id is still unknown; saving as DISABLED"
                )

                account = Account(
                    storage_type=StorageType.TDATA,
                    session_path=session_path,
                    tdata_path=tdata_path,
                    status=AccountStatus.DISABLED,
                    error_text="Valid session, but TG User ID could not be determined",
                )
                session.add(account)
                await session.flush()
                await session.refresh(account)

                # Чистим распаковку tdata (converted session лежит отдельно в INBOX_DIR)
                shutil.rmtree(extract_dir, ignore_errors=True)

                return (
                    False,
                    (
                        f"⚠️ tdata импортирован, но не удалось определить TG User ID\n\n"
                        f"📱 ID: {account.id}\n"
                        f"🔴 Статус: DISABLED\n\n"
                        f"Попробуйте импортировать заново или конвертировать на машине с доступом к Telegram."
                    ),
                    account,
                )

            if validation.success:
                # Проверка дубликата
                existing = await check_duplicate(session, validation.tg_user_id)

                # Если в БД уже есть старые записи с tg_user_id=NULL — попробуем склеить по телефону.
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
                # Перемещаем session в постоянное хранилище (путь одинаковый)
                final_dir = os.path.join(SESSIONS_DIR, str(validation.tg_user_id))
                os.makedirs(final_dir, exist_ok=True)
                final_session_path = os.path.join(final_dir, "account.session")

                if existing:
                    # Заменяем session-файл, обновляем запись и НЕ создаём дубль
                    try:
                        if os.path.exists(final_session_path):
                            os.remove(final_session_path)
                    except Exception:
                        pass
                    shutil.move(session_path, final_session_path)

                    existing.session_path = final_session_path
                    existing.tdata_path = tdata_path
                    existing.storage_type = StorageType.TDATA
                    existing.username = validation.username or existing.username
                    existing.phone = validation.phone or existing.phone
                    existing.is_premium = (
                        validation.is_premium
                        if validation.is_premium is not None
                        else existing.is_premium
                    )

                    existing.api_id = (
                        validation.api_id
                        if validation.api_id != settings.api_id
                        else None
                    )
                    existing.api_hash = (
                        validation.api_hash
                        if validation.api_hash != settings.api_hash
                        else None
                    )
                    existing.error_text = None

                    await session.flush()
                    await session.refresh(existing)

                    # Очистка временных файлов
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    return True, f"✅ Аккаунт обновлён (ID: {existing.id})", existing

                # Перемещаем session в постоянное хранилище (новый аккаунт)

                final_dir = os.path.join(SESSIONS_DIR, str(validation.tg_user_id))
                os.makedirs(final_dir, exist_ok=True)
                final_session_path = os.path.join(final_dir, "account.session")

                shutil.move(session_path, final_session_path)

                # Сохраняем api_id/api_hash только если они отличаются от глобальных настроек
                save_api_id = (
                    validation.api_id if validation.api_id != settings.api_id else None
                )
                save_api_hash = (
                    validation.api_hash
                    if validation.api_hash != settings.api_hash
                    else None
                )

                # Создаём аккаунт со статусом FREE
                account = Account(
                    tg_user_id=validation.tg_user_id,
                    username=validation.username,
                    phone=validation.phone,
                    storage_type=StorageType.TDATA,
                    session_path=final_session_path,
                    tdata_path=tdata_path,
                    status=AccountStatus.FREE,
                    is_premium=validation.is_premium,
                    api_id=save_api_id,
                    api_hash=save_api_hash,
                    error_text=None,
                )
                session.add(account)
                await session.flush()
                await session.refresh(account)

                logger.info(
                    f"tdata account created: id={account.id}, tg_user_id={validation.tg_user_id}, api_id={save_api_id or 'default'}"
                )

                # Автоматически назначаем прокси по стране аккаунта
                proxy_info = ""
                assigned_proxy = await proxy_service.assign_proxy_to_account(
                    session, account.id
                )
                if assigned_proxy:
                    country_flag = proxy_service.get_country_flag(
                        assigned_proxy.country
                    )
                    proxy_info = f"\n🌐 Прокси: {country_flag} `{assigned_proxy.host}:{assigned_proxy.port}`"
                    logger.info(
                        f"Auto-assigned proxy {assigned_proxy.id} ({assigned_proxy.country}) to account {account.id}"
                    )

                # Формируем строку API источника
                api_source_str = (
                    "📦 JSON" if validation.api_source == "json" else "⚙️ .env.example"
                )
                api_display = (
                    f"{validation.api_id}"[:8] + "..." if validation.api_id else "—"
                )

                premium_mark = "⭐ " if validation.is_premium else ""
                return (
                    True,
                    (
                        f"✅ **tdata успешно импортирован!**\n\n"
                        f"📱 ID: {account.id}\n"
                        f"🆔 TG User ID: {validation.tg_user_id}\n"
                        f"👤 Username: @{validation.username or 'нет'}\n"
                        f"📞 Phone: {validation.phone or 'скрыт'}"
                        f"{proxy_info}\n"
                        f"🔑 API ID: `{api_display}` ({api_source_str})\n"
                        f"{premium_mark}Premium: {'Да' if validation.is_premium else 'Нет'}\n"
                        f"🟢 Статус: FREE (готов к выдаче)"
                    ),
                    account,
                )
            else:
                # Сессия невалидна после конвертации
                logger.warning(f"Converted session invalid: {validation.error}")

                # Сохраняем как disabled
                account = Account(
                    storage_type=StorageType.TDATA,
                    session_path=session_path,
                    tdata_path=tdata_path,
                    status=AccountStatus.DISABLED,
                    error_text=f"Converted but invalid: {validation.error}",
                )
                session.add(account)
                await session.flush()
                await session.refresh(account)

                return (
                    False,
                    (
                        f"⚠️ tdata конвертирован, но сессия невалидна\n\n"
                        f"📱 ID: {account.id}\n"
                        f"❌ Ошибка: {validation.error}\n"
                        f"🔴 Статус: DISABLED"
                    ),
                    account,
                )

        else:
            # Конвертация не удалась - сохраняем как needs_conversion
            account = Account(
                storage_type=StorageType.TDATA,
                tdata_path=tdata_path,
                session_path=None,
                status=AccountStatus.NEEDS_CONVERSION,
                error_text=convert_msg,
            )
            session.add(account)
            await session.flush()
            await session.refresh(account)

            logger.info(f"tdata saved for later conversion: id={account.id}")

            return (
                True,
                (
                    f"📦 **tdata импортирован**\n\n"
                    f"📱 ID: {account.id}\n"
                    f"📁 Путь: {tdata_path}\n"
                    f"🟡 Статус: NEEDS_CONVERSION\n\n"
                    f"⚠️ {convert_msg}\n\n"
                    f"Используйте `/convert_tdata {account.id}` для повторной попытки."
                ),
                account,
            )

    except zipfile.BadZipFile:
        return False, "❌ Повреждённый ZIP архив", None

    except Exception as e:
        logger.exception(f"Import tdata error: {e}")
        # Очистка при ошибке
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
        return False, f"❌ Ошибка импорта: {e}", None


async def attempt_conversion(
    session: AsyncSession, account_id: int
) -> Tuple[bool, str]:
    """
    Попытка конвертации tdata для существующего аккаунта.

    Returns:
        (success, message)
    """
    account = await session.get(Account, account_id)

    if not account:
        return False, "❌ Аккаунт не найден"

    if account.storage_type != StorageType.TDATA:
        return False, "❌ Аккаунт не является tdata"

    if not account.tdata_path or not os.path.exists(account.tdata_path):
        return False, "❌ Путь к tdata не найден или удалён"

    if account.status == AccountStatus.FREE and account.session_path:
        return False, "ℹ️ Аккаунт уже сконвертирован и готов к использованию"

    # Пробуем конвертировать
    success, msg, session_path = await convert_tdata_to_session(account.tdata_path)

    if success and session_path:
        # Валидируем (skip_connect=True чтобы не убить сессию)
        validation = await validate_session(session_path, skip_connect=True)

        if validation.success:
            # Проверка дубликата (если tg_user_id ещё не установлен)
            if not account.tg_user_id:
                existing = await check_duplicate(session, validation.tg_user_id)
                if existing and existing.id != account.id:
                    os.remove(session_path)
                    return (
                        False,
                        f"❌ Аккаунт tg_user_id={validation.tg_user_id} уже существует (ID: {existing.id})",
                    )

            # Перемещаем session
            final_dir = os.path.join(SESSIONS_DIR, str(validation.tg_user_id))
            os.makedirs(final_dir, exist_ok=True)
            final_session_path = os.path.join(final_dir, "account.session")

            if os.path.exists(final_session_path):
                os.remove(final_session_path)
            shutil.move(session_path, final_session_path)

            # Обновляем аккаунт
            account.tg_user_id = validation.tg_user_id
            account.username = validation.username
            account.phone = validation.phone
            account.is_premium = validation.is_premium
            account.session_path = final_session_path
            account.status = AccountStatus.FREE
            account.error_text = None
            await session.flush()

            premium_mark = "⭐ " if validation.is_premium else ""
            return True, (
                f"✅ **Конвертация успешна!**\n\n"
                f"📱 ID: {account.id}\n"
                f"🆔 TG User ID: {validation.tg_user_id}\n"
                f"👤 Username: @{validation.username or 'нет'}\n"
                f"📞 Phone: {validation.phone or 'скрыт'}\n"
                f"{premium_mark}Premium: {'Да' if validation.is_premium else 'Нет'}\n"
                f"🟢 Статус: FREE"
            )
        else:
            account.error_text = f"Converted but invalid: {validation.error}"
            account.status = AccountStatus.DISABLED
            await session.flush()
            return False, f"⚠️ Сконвертировано, но сессия невалидна: {validation.error}"

    account.error_text = msg
    await session.flush()
    return False, f"❌ {msg}"
