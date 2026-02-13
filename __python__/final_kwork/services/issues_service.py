"""
Сервис для работы с заявками (issues).
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Issue, IssueStatus, User, UserRole, Account

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession, 
    tg_id: int, 
    username: str | None = None,
    full_name: str | None = None
) -> User:
    """Получить или создать пользователя."""
    stmt = select(User).where(User.tg_id == tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            tg_id=tg_id,
            username=username,
            full_name=full_name,
            role=UserRole.MANAGER
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        logger.info(f"New user created: tg_id={tg_id}")
    else:
        # Обновляем username если изменился
        if username and user.username != username:
            user.username = username
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        await session.flush()
    
    return user


async def create_issue(
    session: AsyncSession,
    user: User,
    ip_address: str | None = None,
    risk_score: float | None = None
) -> Issue:
    """Создать новую заявку."""
    issue = Issue(
        user_id=user.id,
        status=IssueStatus.PENDING,
        ip_address=ip_address,
        risk_score=risk_score
    )
    session.add(issue)
    await session.flush()
    await session.refresh(issue)
    logger.info(f"Issue created: id={issue.id}, user_id={user.id}")
    return issue


async def get_issue_by_id(session: AsyncSession, issue_id: int) -> Optional[Issue]:
    """Получить заявку по ID с подгруженными связями."""
    stmt = select(Issue).where(Issue.id == issue_id).options(
        selectinload(Issue.user),
        selectinload(Issue.account)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def approve_issue(
    session: AsyncSession,
    issue: Issue,
    account: Account
) -> None:
    """Одобрить заявку и привязать аккаунт."""
    issue.status = IssueStatus.APPROVED
    issue.approved_at = datetime.utcnow()
    issue.account_id = account.id
    issue.account_was_premium = account.is_premium
    await session.flush()
    logger.info(f"Issue approved: id={issue.id}, account_id={account.id}")


async def reject_issue(session: AsyncSession, issue: Issue) -> None:
    """Отклонить заявку."""
    issue.status = IssueStatus.REJECTED
    issue.rejected_at = datetime.utcnow()
    await session.flush()
    logger.info(f"Issue rejected: id={issue.id}")


async def revoke_issue(session: AsyncSession, issue: Issue) -> None:
    """Отозвать выданный аккаунт."""
    issue.status = IssueStatus.REVOKED
    issue.revoked_at = datetime.utcnow()
    await session.flush()
    logger.info(f"Issue revoked: id={issue.id}")


async def set_confirmation_code(session: AsyncSession, issue: Issue, code: str) -> None:
    """Сохранить код подтверждения."""
    issue.confirmation_code = code
    await session.flush()


async def get_pending_issues(session: AsyncSession) -> List[Issue]:
    """Получить все ожидающие заявки."""
    stmt = select(Issue).where(
        Issue.status == IssueStatus.PENDING
    ).options(selectinload(Issue.user)).order_by(Issue.requested_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_active_issues(session: AsyncSession) -> List[Issue]:
    """Получить все активные выдачи (APPROVED)."""
    stmt = select(Issue).where(
        Issue.status == IssueStatus.APPROVED,
        # Считаем активной выдачей только после того, как код реально отправлен менеджеру
        Issue.confirmation_code.is_not(None),
    ).options(
        selectinload(Issue.user),
        selectinload(Issue.account)
    ).order_by(Issue.approved_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_active_by_user(session: AsyncSession, user_id: int) -> int:
    """Подсчитать количество активных выдач у пользователя."""
    from sqlalchemy import func
    stmt = select(func.count()).select_from(Issue).where(
        Issue.user_id == user_id,
        Issue.status == IssueStatus.APPROVED,
        Issue.confirmation_code.is_not(None),
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_all_issues(session: AsyncSession, limit: int = 50) -> List[Issue]:
    """Получить историю заявок."""
    stmt = select(Issue).options(
        selectinload(Issue.user),
        selectinload(Issue.account)
    ).order_by(Issue.requested_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_pending_by_user(session: AsyncSession, user_id: int) -> List[Issue]:
    """Получить ожидающие заявки пользователя."""
    stmt = select(Issue).where(
        Issue.user_id == user_id,
        Issue.status == IssueStatus.PENDING
    ).order_by(Issue.requested_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_history(session: AsyncSession, user_id: int) -> List[dict]:
    """Получить историю пользователя для AI-анализа."""
    stmt = select(Issue).where(Issue.user_id == user_id).order_by(Issue.requested_at.desc())
    result = await session.execute(stmt)
    issues = result.scalars().all()
    
    return [
        {
            "id": i.id,
            "status": i.status.value,
            "requested_at": i.requested_at.isoformat() if i.requested_at else None,
            "revoked_at": i.revoked_at.isoformat() if i.revoked_at else None
        }
        for i in issues
    ]


async def get_account_owner(session: AsyncSession, account_id: int) -> Optional[dict]:
    """
    Получить информацию о владельце аккаунта (если выдан).
    
    Returns:
        dict с user_id, tg_id, username, issued_at или None
    """
    stmt = select(Issue).where(
        Issue.account_id == account_id,
        Issue.status == IssueStatus.APPROVED,
        Issue.confirmation_code.is_not(None),
    ).options(selectinload(Issue.user)).order_by(Issue.approved_at.desc()).limit(1)
    
    result = await session.execute(stmt)
    issue = result.scalar_one_or_none()
    
    if not issue or not issue.user:
        return None
    
    return {
        "issue_id": issue.id,
        "user_id": issue.user.id,
        "tg_id": issue.user.tg_id,
        "username": issue.user.username,
        "full_name": issue.user.full_name,
        "issued_at": issue.approved_at,
    }


async def get_managers_with_accounts(session: AsyncSession) -> List[dict]:
    """
    Получить список менеджеров, у которых есть активные аккаунты.
    
    Returns:
        Список dict: user_id, tg_id, username, full_name, accounts_count
    """
    from sqlalchemy import func
    
    # Подзапрос для подсчёта активных выдач
    stmt = (
        select(
            User.id,
            User.tg_id,
            User.username,
            User.full_name,
            func.count(Issue.id).label("accounts_count")
        )
        .join(Issue, Issue.user_id == User.id)
        .where(
            Issue.status == IssueStatus.APPROVED,
            Issue.confirmation_code.is_not(None),
        )
        .group_by(User.id)
        .order_by(func.count(Issue.id).desc())
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        {
            "user_id": row.id,
            "tg_id": row.tg_id,
            "username": row.username,
            "full_name": row.full_name,
            "accounts_count": row.accounts_count,
        }
        for row in rows
    ]


async def get_user_active_issues(session: AsyncSession, user_id: int) -> List[Issue]:
    """
    Получить активные выдачи конкретного менеджера.
    
    Args:
        user_id: Внутренний ID пользователя (не tg_id)
    
    Returns:
        Список Issue со связанными account
    """
    stmt = select(Issue).where(
        Issue.user_id == user_id,
        Issue.status == IssueStatus.APPROVED,
        Issue.confirmation_code.is_not(None),
    ).options(
        selectinload(Issue.user),
        selectinload(Issue.account)
    ).order_by(Issue.approved_at.desc())
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Получить пользователя по внутреннему ID."""
    return await session.get(User, user_id)
