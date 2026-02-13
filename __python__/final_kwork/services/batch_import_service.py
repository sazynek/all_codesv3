"""
Сервис пакетного импорта сессий из ZIP-архива.

Поддерживает:
- Импорт нескольких .session файлов из одного ZIP
- Автоматический поиск JSON с api_id/api_hash рядом с каждой сессией
- Различные форматы JSON (плоский, вложенный, разные ключи)
- Отчёт об импорте с детализацией
"""

import json
import logging
import os
import shutil
import uuid
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import Account, AccountStatus, StorageType
from services.session_import_service import (
    INBOX_DIR,
    SESSIONS_DIR,
    ensure_directories,
    validate_session,
    check_duplicate,
    extract_api_credentials_from_dict,
)
from services import proxy_service

logger = logging.getLogger(__name__)

# Максимальный размер ZIP (500 MB)
MAX_ZIP_SIZE = 500 * 1024 * 1024


@dataclass
class SessionImportItem:
    """Результат импорта одной сессии."""

    session_path: str
    session_name: str
    success: bool
    account_id: Optional[int] = None
    tg_user_id: Optional[int] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    api_id: Optional[int] = None
    api_hash_masked: Optional[str] = None
    api_source: str = "none"  # "json", "env", "none"
    error: Optional[str] = None
    is_duplicate: bool = False


@dataclass
class BatchImportReport:
    """Отчёт о пакетном импорте."""

    total_sessions_found: int = 0
    successfully_imported: int = 0
    with_api_credentials: int = 0
    with_env_fallback: int = 0
    duplicates_skipped: int = 0
    errors: int = 0
    items: List[SessionImportItem] = field(default_factory=list)

    def add_success(self, item: SessionImportItem):
        """Добавить успешный импорт."""
        self.items.append(item)
        self.successfully_imported += 1
        if item.api_source == "json":
            self.with_api_credentials += 1
        elif item.api_source == "env":
            self.with_env_fallback += 1

    def add_error(self, item: SessionImportItem):
        """Добавить ошибку."""
        self.items.append(item)
        if item.is_duplicate:
            self.duplicates_skipped += 1
        else:
            self.errors += 1

    def format_message(self) -> str:
        """Форматирование отчёта для вывода в чат."""
        lines = [
            "📦 **Отчёт импорта ZIP**\n",
            f"📊 Найдено сессий: {self.total_sessions_found}",
            f"✅ Успешно импортировано: {self.successfully_imported}",
            f"🔑 С API из JSON: {self.with_api_credentials}",
            f"⚙️ Fallback на .env.example: {self.with_env_fallback}",
        ]

        if self.duplicates_skipped > 0:
            lines.append(f"⏭️ Пропущено дубликатов: {self.duplicates_skipped}")

        if self.errors > 0:
            lines.append(f"❌ Ошибок: {self.errors}")

        # Детали успешных
        if self.successfully_imported > 0:
            lines.append("\n**Импортированные аккаунты:**")
            for item in self.items:
                if item.success:
                    api_mark = "🔑" if item.api_source == "json" else "⚙️"
                    username_str = f"@{item.username}" if item.username else ""
                    lines.append(
                        f"• #{item.account_id} {username_str} "
                        f"`{item.phone or item.tg_user_id or 'N/A'}` {api_mark}"
                    )

        # Детали ошибок
        error_items = [i for i in self.items if not i.success and not i.is_duplicate]
        if error_items:
            lines.append("\n**Ошибки:**")
            for item in error_items[:5]:  # Показываем первые 5 ошибок
                lines.append(f"• `{item.session_name}`: {item.error}")
            if len(error_items) > 5:
                lines.append(f"  ... и ещё {len(error_items) - 5} ошибок")

        # Дубликаты
        dup_items = [i for i in self.items if i.is_duplicate]
        if dup_items:
            lines.append(f"\n**Дубликаты (пропущены):** {len(dup_items)} шт.")

        return "\n".join(lines)


def extract_zip(zip_path: str, dst_dir: str) -> Tuple[bool, str]:
    """
    Распаковать ZIP-архив.

    Args:
        zip_path: Путь к ZIP файлу
        dst_dir: Целевая директория

    Returns:
        (success, error_message)
    """
    try:
        os.makedirs(dst_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Проверка на ZIP bomb
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > MAX_ZIP_SIZE * 10:
                return (
                    False,
                    f"Архив слишком большой после распаковки ({total_size // 1024 // 1024} MB)",
                )

            zf.extractall(dst_dir)

        return True, ""

    except zipfile.BadZipFile:
        return False, "Повреждённый ZIP-архив"
    except Exception as e:
        return False, f"Ошибка распаковки: {e}"


def find_session_files(root_dir: str) -> List[str]:
    """
    Найти все .session файлы в директории (рекурсивно).

    Args:
        root_dir: Корневая директория для поиска

    Returns:
        Список путей к .session файлам
    """
    session_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".session"):
                session_files.append(os.path.join(dirpath, filename))

    return session_files


def find_matching_json(session_path: str) -> Optional[str]:
    """
    Найти JSON файл с api_id/api_hash для данной сессии.

    Стратегия поиска:
    1. Файл с тем же именем: name.session -> name.json
    2. Приоритетные имена в той же папке: api.json, config.json, etc.
    3. Любой .json в той же папке с валидными credentials

    Args:
        session_path: Путь к .session файлу

    Returns:
        Путь к JSON файлу или None
    """
    session_dir = os.path.dirname(session_path)
    session_basename = os.path.splitext(os.path.basename(session_path))[0]

    # 1. Точное совпадение имени: name.session -> name.json
    matching_json = os.path.join(session_dir, f"{session_basename}.json")
    if os.path.exists(matching_json):
        return matching_json

    # 2. Приоритетные имена
    priority_names = settings.account_json_filenames_list
    for name in priority_names:
        json_path = os.path.join(session_dir, name)
        if os.path.exists(json_path):
            # Проверяем, что JSON содержит credentials
            creds = extract_api_credentials(json_path)
            if creds:
                return json_path

    # 3. Любой .json файл с credentials
    try:
        for filename in os.listdir(session_dir):
            if filename.lower().endswith(".json"):
                json_path = os.path.join(session_dir, filename)
                creds = extract_api_credentials(json_path)
                if creds:
                    return json_path
    except OSError:
        pass

    return None


def extract_api_credentials(json_path: str) -> Optional[Tuple[int, str]]:
    """
    Извлечь api_id и api_hash из JSON файла.

    Args:
        json_path: Путь к JSON файлу

    Returns:
        (api_id, api_hash) или None
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return extract_api_credentials_from_dict(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {json_path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to read {json_path}: {e}")
        return None


def mask_api_hash(api_hash: str) -> str:
    """Маскировать api_hash для безопасного отображения."""
    if not api_hash or len(api_hash) < 8:
        return "***"
    return f"{api_hash[:4]}...{api_hash[-4:]}"


async def import_one_session(
    db_session: AsyncSession,
    session_path: str,
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    api_source: str = "none",
) -> SessionImportItem:
    """
    Импортировать одну сессию.

    Args:
        db_session: SQLAlchemy async session
        session_path: Путь к .session файлу
        api_id: API ID (если найден в JSON)
        api_hash: API Hash (если найден в JSON)
        api_source: Источник credentials ("json", "env", "none")

    Returns:
        SessionImportItem с результатом
    """
    session_name = os.path.splitext(os.path.basename(session_path))[0]

    item = SessionImportItem(
        session_path=session_path,
        session_name=session_name,
        success=False,
        api_source=api_source,
    )

    # Если нет credentials и разрешён fallback
    if api_id is None or api_hash is None:
        if settings.fallback_env_api and settings.api_id and settings.api_hash:
            api_id = settings.api_id
            api_hash = settings.api_hash
            item.api_source = "env"
        else:
            # Импортируем без credentials (fallback при использовании)
            item.api_source = "none"

    if api_id:
        item.api_id = api_id
    if api_hash:
        item.api_hash_masked = mask_api_hash(api_hash)

    try:
        logger.info(f"Validating session: {session_path}")

        # Валидируем сессию с credentials
        # skip_connect=True — НЕ подключаемся к Telegram, только читаем данные из файла
        # Это безопасно: не убиваем сессию при импорте
        validation = await validate_session(
            session_path, api_id=api_id, api_hash=api_hash, skip_connect=True
        )

        logger.info(
            f"Validation result: success={validation.success}, tg_user_id={validation.tg_user_id}, error={validation.error}"
        )

        if not validation.success:
            item.error = validation.error
            return item

        item.tg_user_id = validation.tg_user_id  # Может быть None — это нормально
        item.username = validation.username
        item.phone = validation.phone

        # Проверка дубликата (только если есть tg_user_id)
        if validation.tg_user_id:
            existing = await check_duplicate(db_session, validation.tg_user_id)
            if existing:
                item.error = f"Дубликат (ID: {existing.id})"
                item.is_duplicate = True
                return item

        # Определяем путь хранения:
        # - Если есть tg_user_id: storage/sessions/{tg_user_id}/
        # - Если нет: storage/sessions/pending_{uuid}/
        if validation.tg_user_id:
            storage_id = str(validation.tg_user_id)
        else:
            # Генерируем временный ID для хранения
            import uuid as uuid_module

            storage_id = f"pending_{uuid_module.uuid4().hex[:8]}"
            logger.info(f"No user_id, using temporary storage: {storage_id}")

        final_dir = os.path.join(SESSIONS_DIR, storage_id)
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, "account.session")

        shutil.copy2(session_path, final_path)

        # Сохраняем api_id/api_hash только если они из JSON
        save_api_id = api_id if item.api_source == "json" else None
        save_api_hash = api_hash if item.api_source == "json" else None

        # Fingerprint из validation результата
        fp = validation.fingerprint

        # Создаём аккаунт
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
            device_model=fp.device_model if fp else None,
            system_version=fp.system_version if fp else None,
            app_version=fp.app_version if fp else None,
            lang_code=fp.lang_code if fp else None,
            system_lang_code=fp.system_lang_code if fp else None,
            error_text=None,
        )
        db_session.add(account)
        await db_session.flush()
        await db_session.refresh(account)

        item.account_id = account.id
        item.success = True

        # Автоматически назначаем прокси
        assigned_proxy = await proxy_service.assign_proxy_to_account(
            db_session, account.id
        )
        if assigned_proxy:
            logger.info(
                f"Auto-assigned proxy {assigned_proxy.id} to account {account.id}"
            )

        user_id_status = (
            validation.tg_user_id or "pending (будет получен при подключении)"
        )
        phone_status = validation.phone or "pending"
        logger.info(
            f"Batch import: account #{account.id} created, "
            f"tg_user_id={user_id_status}, phone={phone_status}, api_source={item.api_source}"
        )

        return item

    except Exception as e:
        logger.exception(f"Error importing session {session_path}: {e}")
        item.error = str(e)
        return item


async def import_zip(
    db_session: AsyncSession, zip_data: bytes, original_filename: str
) -> BatchImportReport:
    """
    Импорт нескольких сессий из ZIP-архива.

    Args:
        db_session: SQLAlchemy async session
        zip_data: Содержимое ZIP-архива
        original_filename: Оригинальное имя файла

    Returns:
        BatchImportReport с результатами
    """
    ensure_directories()
    report = BatchImportReport()

    # Проверка размера
    if len(zip_data) > MAX_ZIP_SIZE:
        report.errors = 1
        report.items.append(
            SessionImportItem(
                session_path="",
                session_name="",
                success=False,
                error=f"ZIP слишком большой (макс. {MAX_ZIP_SIZE // 1024 // 1024} MB)",
            )
        )
        return report

    # Временные пути
    temp_id = str(uuid.uuid4())
    zip_path = os.path.join(INBOX_DIR, f"{temp_id}.zip")
    extract_dir = os.path.join(INBOX_DIR, f"batch_{temp_id}")

    try:
        # Сохраняем ZIP
        os.makedirs(INBOX_DIR, exist_ok=True)
        with open(zip_path, "wb") as f:
            f.write(zip_data)

        logger.info(f"ZIP saved: {zip_path}, size: {len(zip_data)} bytes")

        # Распаковываем
        success, error = extract_zip(zip_path, extract_dir)
        if not success:
            report.errors = 1
            report.items.append(
                SessionImportItem(
                    session_path="", session_name="", success=False, error=error
                )
            )
            return report

        # Ищем .session файлы
        session_files = find_session_files(extract_dir)
        report.total_sessions_found = len(session_files)

        if not session_files:
            report.errors = 1
            report.items.append(
                SessionImportItem(
                    session_path="",
                    session_name="",
                    success=False,
                    error="В архиве не найдено .session файлов",
                )
            )
            return report

        logger.info(f"Found {len(session_files)} session files in ZIP")

        # Импортируем каждую сессию
        for session_path in session_files:
            # Ищем JSON с credentials
            json_path = find_matching_json(session_path)
            api_id = None
            api_hash = None
            api_source = "none"

            if json_path:
                creds = extract_api_credentials(json_path)
                if creds:
                    api_id, api_hash = creds
                    api_source = "json"
                    logger.info(
                        f"Found credentials for {session_path}: api_id={api_id}"
                    )

            # Импортируем
            item = await import_one_session(
                db_session,
                session_path,
                api_id=api_id,
                api_hash=api_hash,
                api_source=api_source,
            )

            if item.success:
                report.add_success(item)
            else:
                report.add_error(item)

        return report

    except Exception as e:
        logger.exception(f"Batch import error: {e}")
        report.errors += 1
        report.items.append(
            SessionImportItem(
                session_path="",
                session_name="",
                success=False,
                error=f"Критическая ошибка: {e}",
            )
        )
        return report

    finally:
        # Очистка временных файлов
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")
