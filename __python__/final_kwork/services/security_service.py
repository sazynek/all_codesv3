"""
Сервис безопасности: проверка лимитов и валидация запросов.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Issue, IssueStatus, User
from config import settings

logger = logging.getLogger(__name__)

# In-memory кэш для cooldown (простое решение)
_last_request_cache: dict[int, datetime] = {}


async def check_manager_limit(session: AsyncSession, user_id: int) -> Tuple[bool, int]:
    """
    Проверка лимита активных аккаунтов на менеджера.
    
    Args:
        session: Сессия БД
        user_id: ID пользователя
    
    Returns:
        (is_allowed, current_count): Разрешено ли, текущее количество
    """
    # ВАЖНО: считаем «выданным» только тогда, когда менеджеру реально отправили код
    # (confirmation_code заполнен). Это защищает от ситуации, когда админ нажал
    # «Подтвердить», но менеджер ещё не успел войти и код не перехвачен.
    stmt = select(func.count(Issue.id)).where(
        Issue.user_id == user_id,
        Issue.status == IssueStatus.APPROVED,
        Issue.confirmation_code.is_not(None),
    )
    result = await session.execute(stmt)
    count = result.scalar() or 0
    
    allowed = count < settings.max_accounts_per_manager
    if not allowed:
        logger.warning(
            f"Manager limit exceeded: user_id={user_id}, "
            f"current={count}, max={settings.max_accounts_per_manager}"
        )
    
    return allowed, count


async def check_cooldown(user_id: int) -> Tuple[bool, int]:
    """
    Проверка cooldown между запросами.
    
    Args:
        user_id: ID пользователя (внутренний, не tg_id)
    
    Returns:
        (is_allowed, remaining_seconds): Разрешено ли, сколько секунд осталось ждать
    """
    if settings.request_cooldown_seconds <= 0:
        return True, 0
    
    last_request = _last_request_cache.get(user_id)
    if not last_request:
        return True, 0
    
    elapsed = (datetime.utcnow() - last_request).total_seconds()
    remaining = settings.request_cooldown_seconds - int(elapsed)
    
    if remaining <= 0:
        return True, 0
    
    logger.debug(f"Cooldown active: user_id={user_id}, remaining={remaining}s")
    return False, remaining


def update_last_request(user_id: int) -> None:
    """Обновить время последнего запроса."""
    _last_request_cache[user_id] = datetime.utcnow()


async def validate_request(
    session: AsyncSession, 
    user_id: int
) -> Tuple[bool, str]:
    """
    Комплексная проверка запроса на выдачу аккаунта.
    
    Проверяет:
    1. Лимит активных аккаунтов на менеджера
    2. Cooldown между запросами (60 сек по умолчанию)
    
    НЕ блокирует за неудачные попытки!
    
    Args:
        session: Сессия БД
        user_id: ID пользователя (внутренний)
    
    Returns:
        (is_valid, error_message): Валиден ли запрос, сообщение об ошибке
    """
    # 1. Проверяем лимит активных аккаунтов на менеджера
    limit_ok, current_count = await check_manager_limit(session, user_id)
    if not limit_ok:
        return False, (
            f"Достигнут лимит аккаунтов ({current_count}/{settings.max_accounts_per_manager})"
        )
    
    # 2. Проверяем cooldown между запросами (анти-спам)
    cooldown_ok, remaining = await check_cooldown(user_id)
    if not cooldown_ok:
        return False, (
            f"Подождите {remaining} сек. перед следующим запросом"
        )
    
    # Обновляем время последнего запроса
    update_last_request(user_id)
    
    return True, ""
