"""
Сервис для работы с аккаунтами.

Включает защиту от race condition при выдаче аккаунтов.
"""

import logging
import os
import shutil
from typing import List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Account, AccountStatus, StorageType

logger = logging.getLogger(__name__)


async def get_free_account_with_lock(
    session: AsyncSession, _retry_count: int = 0
) -> Optional[Account]:
    """
    Получить и заблокировать свободный аккаунт для выдачи.

    Использует атомарный UPDATE с WHERE для защиты от race condition.
    Два админа не смогут выдать один аккаунт одновременно.

    Args:
        session: Сессия БД
        _retry_count: Внутренний счётчик попыток (не передавать вручную)

    Returns:
        Account если найден и заблокирован, None если нет свободных.
    """
    MAX_RETRIES = 5

    if _retry_count >= MAX_RETRIES:
        logger.error(
            f"[get_free_account_with_lock] max retries exceeded ({MAX_RETRIES})"
        )
        return None

    stmt = (
        select(Account.id)
        .where(Account.status == AccountStatus.FREE, Account.session_path.isnot(None))
        .limit(1)
    )

    result = await session.execute(stmt)
    account_id = result.scalar_one_or_none()

    if not account_id:
        logger.debug("[get_free_account_with_lock] no free accounts")
        return None

    # Атомарно обновляем статус (защита от race condition)
    update_stmt = (
        update(Account)
        .where(Account.id == account_id, Account.status == AccountStatus.FREE)
        .values(status=AccountStatus.ASSIGNED)
        .returning(Account.id)
    )

    update_result = await session.execute(update_stmt)
    updated_id = update_result.scalar_one_or_none()

    if not updated_id:
        # Гонка — пробуем ещё раз с увеличенным счётчиком
        logger.warning(
            f"[get_free_account_with_lock] race for account_id={account_id}, retry {_retry_count + 1}"
        )
        return await get_free_account_with_lock(session, _retry_count + 1)

    # Получаем полный объект
    account = await session.get(Account, updated_id)
    logger.info(f"[get_free_account_with_lock] locked account_id={account.id}")

    return account


async def get_account_by_id(
    session: AsyncSession, account_id: int
) -> Optional[Account]:
    """Получить аккаунт по ID."""
    return await session.get(Account, account_id)


async def get_all_accounts(session: AsyncSession) -> List[Account]:
    """Получить все аккаунты, отсортированные по статусу и ID."""
    stmt = select(Account).order_by(Account.status, Account.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def release_account(session: AsyncSession, account: Account) -> None:
    """Освободить аккаунт (вернуть статус FREE)."""
    account.status = AccountStatus.FREE
    await session.flush()
    logger.info(f"[release_account] account_id={account.id} released")


async def disable_account(
    session: AsyncSession, account: Account, error_text: Optional[str] = None
) -> None:
    """Отключить проблемный аккаунт."""
    account.status = AccountStatus.DISABLED
    if error_text:
        account.error_text = error_text
    await session.flush()
    logger.warning(f"[disable_account] account_id={account.id}, reason={error_text}")


async def delete_account(
    session: AsyncSession, account: Account, delete_files: bool = True
) -> Tuple[bool, str]:
    """
    Удалить аккаунт.

    Args:
        session: DB session
        account: Аккаунт для удаления
        delete_files: Удалять ли файлы сессии/tdata

    Returns:
        (success, message)
    """
    if account.status == AccountStatus.ASSIGNED:
        return False, "Аккаунт сейчас выдан. Сначала отзовите его."

    account_id = account.id
    identifier = account.phone or account.tg_user_id or "unknown"

    # Удаляем файлы
    if delete_files:
        if account.session_path and os.path.exists(account.session_path):
            try:
                os.remove(account.session_path)
                # Удаляем папку если пуста
                folder = os.path.dirname(account.session_path)
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
            except OSError as e:
                logger.warning(f"[delete_account] failed to delete session: {e}")

        if account.tdata_path and os.path.exists(account.tdata_path):
            try:
                shutil.rmtree(account.tdata_path, ignore_errors=True)
            except OSError as e:
                logger.warning(f"[delete_account] failed to delete tdata: {e}")

    # Удаляем из БД
    await session.delete(account)
    await session.flush()

    logger.info(f"[delete_account] account_id={account_id} deleted")
    return True, f"Аккаунт #{account_id} ({identifier}) удалён"


async def add_account(
    session: AsyncSession,
    phone: str,
    session_path: str,
    is_premium: bool = False,
    tg_user_id: Optional[int] = None,
    username: Optional[str] = None,
) -> Account:
    """Добавить новый аккаунт вручную с проверкой дубликатов."""

    # 1. ПРОВЕРКА ДУБЛИКАТА
    is_dup = await is_account_duplicate(session, session_path=session_path, phone=phone)

    if is_dup:
        # Находим существующий аккаунт
        from sqlalchemy import or_

        stmt = (
            select(Account)
            .where(
                or_(
                    Account.phone == phone,
                    Account.session_path == os.path.abspath(session_path),
                )
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        existing_account = result.scalar_one_or_none()

        if existing_account:
            logger.info(
                f"[add_account] DUPLICATE: phone={phone} already exists as account_id={existing_account.id}"
            )
            return existing_account  # Возвращаем существующий аккаунт

    account = Account(
        phone=phone,
        session_path=session_path,
        is_premium=is_premium,
        status=AccountStatus.FREE,
        storage_type=StorageType.TELETHON_SESSION,
        tg_user_id=tg_user_id,
        username=username,
    )
    session.add(account)
    await session.flush()
    await session.refresh(account)

    logger.info(f"[add_account] NEW: phone={phone}, account_id={account.id}")
    return account


# =========================
# CHECK ON DUPLICATE
# =========================
async def is_account_duplicate(
    session: AsyncSession,
    session_path: Optional[str] = None,
    session_string: Optional[str] = None,
    tdata_path: Optional[str] = None,
    phone: Optional[str] = None,
) -> bool:
    """
    Проверяет, существует ли уже такой аккаунт в БД.
    Использовать при импорте через сессию или tdata.
    """
    from sqlalchemy import or_

    conditions = []

    if session_path and os.path.exists(session_path):
        # Нормализуем путь для сравнения
        abs_path = os.path.abspath(session_path)
        conditions.append(Account.session_path == abs_path)

    if session_string:
        conditions.append(Account.session_string == session_string)

    if tdata_path and os.path.exists(tdata_path):
        abs_tdata = os.path.abspath(tdata_path)
        conditions.append(Account.tdata_path == abs_tdata)

    if phone:
        conditions.append(Account.phone == phone)

    if not conditions:
        return False

    stmt = select(Account).where(or_(*conditions)).limit(1)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(
            f"[is_account_duplicate] Found duplicate: account_id={existing.id}, path={session_path or tdata_path}"
        )

    return existing is not None
