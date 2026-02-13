"""
Сервис статистики системы.
"""
import logging
from dataclasses import dataclass
from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Account, AccountStatus, Issue, IssueStatus, User
from services import telethon_workers

logger = logging.getLogger(__name__)


@dataclass
class SystemStats:
    """Статистика системы."""
    # Аккаунты
    accounts_total: int = 0
    accounts_free: int = 0
    accounts_assigned: int = 0
    accounts_disabled: int = 0
    accounts_needs_conversion: int = 0
    
    # Заявки
    issues_pending: int = 0
    issues_approved: int = 0
    issues_rejected: int = 0
    issues_revoked: int = 0
    
    # Прочее
    users_total: int = 0
    active_workers: int = 0


async def get_system_stats(session: AsyncSession) -> SystemStats:
    """Получить статистику системы."""
    stats = SystemStats()
    
    # Аккаунты по статусам
    accounts_query = await session.execute(
        select(Account.status, func.count(Account.id)).group_by(Account.status)
    )
    acc_by_status: Dict = dict(accounts_query.all())
    
    stats.accounts_free = acc_by_status.get(AccountStatus.FREE, 0)
    stats.accounts_assigned = acc_by_status.get(AccountStatus.ASSIGNED, 0)
    stats.accounts_disabled = acc_by_status.get(AccountStatus.DISABLED, 0)
    stats.accounts_needs_conversion = acc_by_status.get(AccountStatus.NEEDS_CONVERSION, 0)
    stats.accounts_total = sum(acc_by_status.values())
    
    # Заявки по статусам
    issues_query = await session.execute(
        select(Issue.status, func.count(Issue.id)).group_by(Issue.status)
    )
    iss_by_status: Dict = dict(issues_query.all())
    
    stats.issues_pending = iss_by_status.get(IssueStatus.PENDING, 0)
    stats.issues_approved = iss_by_status.get(IssueStatus.APPROVED, 0)
    stats.issues_rejected = iss_by_status.get(IssueStatus.REJECTED, 0)
    stats.issues_revoked = iss_by_status.get(IssueStatus.REVOKED, 0)
    
    # Пользователи
    users_query = await session.execute(select(func.count(User.id)))
    stats.users_total = users_query.scalar() or 0
    
    # Воркеры
    stats.active_workers = telethon_workers.get_active_workers_count()
    
    logger.debug(f"[stats] collected: accounts={stats.accounts_total}, workers={stats.active_workers}")
    
    return stats


def format_stats_message(stats: SystemStats) -> str:
    """Форматировать статистику для отправки."""
    return (
        f"📊 **Статистика системы**\n\n"
        f"**Аккаунты ({stats.accounts_total}):**\n"
        f"  🟢 Свободных: {stats.accounts_free}\n"
        f"  🔵 Выданных: {stats.accounts_assigned}\n"
        f"  🟡 Ждут конверт.: {stats.accounts_needs_conversion}\n"
        f"  🔴 Отключено: {stats.accounts_disabled}\n\n"
        f"**Заявки:**\n"
        f"  ⏳ Ожидают: {stats.issues_pending}\n"
        f"  ✅ Одобрено: {stats.issues_approved}\n"
        f"  ❌ Отклонено: {stats.issues_rejected}\n"
        f"  🔴 Отозвано: {stats.issues_revoked}\n\n"
        f"**Прочее:**\n"
        f"  👥 Пользователей: {stats.users_total}\n"
        f"  ⚙️ Активных воркеров: {stats.active_workers}"
    )
