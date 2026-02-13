"""
Сервис проверки здоровья системы.
Совместимость с Telethon 2.0.
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.telethon_adapter import (
    TelegramClient,
    AuthKeyUnregisteredError,
    RPCError,
)

from config import settings
from db.base import async_session
from db.models import Account, AccountStatus
from services.accounts_service import get_all_accounts

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Результат проверки."""
    name: str
    status: bool  # True = OK, False = FAIL
    details: str
    duration_ms: float


@dataclass
class SystemHealth:
    """Общее здоровье системы."""
    overall: bool
    checks: List[HealthCheckResult]
    timestamp: datetime


async def check_database() -> HealthCheckResult:
    """Проверка подключения к БД."""
    start = datetime.now()
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        duration = (datetime.now() - start).total_seconds() * 1000
        return HealthCheckResult(
            name="database",
            status=True,
            details="SQLite connection OK",
            duration_ms=duration
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"[health] database check failed: {e}")
        return HealthCheckResult(
            name="database",
            status=False,
            details=f"Error: {e}",
            duration_ms=duration
        )


async def check_sessions_folder() -> HealthCheckResult:
    """Проверка папки сессий."""
    start = datetime.now()
    try:
        sessions_dir = settings.sessions_dir
        
        if not os.path.exists(sessions_dir):
            duration = (datetime.now() - start).total_seconds() * 1000
            return HealthCheckResult(
                name="sessions_folder",
                status=False,
                details=f"Folder does not exist: {sessions_dir}",
                duration_ms=duration
            )
        
        # Считаем .session файлы
        session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.session')]
        duration = (datetime.now() - start).total_seconds() * 1000
        
        return HealthCheckResult(
            name="sessions_folder",
            status=True,
            details=f"Found {len(session_files)} session files",
            duration_ms=duration
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"[health] sessions folder check failed: {e}")
        return HealthCheckResult(
            name="sessions_folder",
            status=False,
            details=f"Error: {e}",
            duration_ms=duration
        )


async def check_accounts_consistency() -> HealthCheckResult:
    """Проверка консистентности аккаунтов."""
    start = datetime.now()
    try:
        async with async_session() as session:
            accounts = await get_all_accounts(session)
        
        issues = []
        for acc in accounts:
            # Проверяем наличие session файла
            if acc.session_path:
                session_path = acc.session_path
                if not session_path.endswith('.session'):
                    session_path += '.session'
                
                if not os.path.exists(session_path):
                    issues.append(f"Account {acc.id}: session file missing")
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        if issues:
            return HealthCheckResult(
                name="accounts_consistency",
                status=False,
                details=f"{len(issues)} issues: " + "; ".join(issues[:3]),
                duration_ms=duration
            )
        
        return HealthCheckResult(
            name="accounts_consistency",
            status=True,
            details=f"All {len(accounts)} accounts OK",
            duration_ms=duration
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"[health] accounts consistency check failed: {e}")
        return HealthCheckResult(
            name="accounts_consistency",
            status=False,
            details=f"Error: {e}",
            duration_ms=duration
        )


async def check_telegram_api() -> HealthCheckResult:
    """Проверка доступности Telegram API (без авторизации)."""
    start = datetime.now()
    try:
        # Простая проверка - создаём клиент без авторизации
        # Используем :memory: — это безопасно, т.к. сессия временная
        client = TelegramClient(
            ':memory:',
            settings.api_id,
            settings.api_hash,
            device_model="Windows 10 x64",
            system_version="Windows 10",
            app_version="4.16.8 x64",
            lang_code="en",
            system_lang_code="en-us",
        )
        await client.connect()
        # Проверяем что соединение установлено
        connected = client.is_connected()
        await client.disconnect()
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        return HealthCheckResult(
            name="telegram_api",
            status=connected,
            details="Telegram API accessible" if connected else "Connection failed",
            duration_ms=duration
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"[health] telegram API check failed: {e}")
        return HealthCheckResult(
            name="telegram_api",
            status=False,
            details=f"Error: {e}",
            duration_ms=duration
        )


async def check_single_account(account: Account) -> HealthCheckResult:
    """
    Проверка одного аккаунта.
    
    ВНИМАНИЕ: Эта функция подключается к Telegram и может потенциально
    вызвать отзыв сессии если используется без прокси!
    Рекомендуется отключить или использовать с осторожностью.
    
    Args:
        account: Аккаунт для проверки
    """
    start = datetime.now()
    
    if not account.session_path:
        return HealthCheckResult(
            name=f"account_{account.id}",
            status=False,
            details="No session path",
            duration_ms=0
        )
    
    session_name = account.session_path.replace('.session', '')
    
    # Используем api_id/api_hash аккаунта если есть, иначе глобальные
    use_api_id = account.api_id or settings.api_id
    use_api_hash = account.api_hash or settings.api_hash
    
    # Device fingerprint
    device_model = account.device_model or "Windows 10 x64"
    system_version = account.system_version or "Windows 10"
    app_version = account.app_version or "4.16.8 x64"
    lang_code = account.lang_code or "en"
    system_lang_code = account.system_lang_code or "en-us"
    
    try:
        client = TelegramClient(
            session_name,
            use_api_id,
            use_api_hash,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version,
            lang_code=lang_code,
            system_lang_code=system_lang_code,
        )
        await client.connect()
        
        try:
            authorized = await client.is_user_authorized()
            
            if authorized:
                me = await client.get_me()
                phone = me.phone if me else "unknown"
                duration = (datetime.now() - start).total_seconds() * 1000
                
                return HealthCheckResult(
                    name=f"account_{account.id}",
                    status=True,
                    details=f"Authorized, phone: +{phone}",
                    duration_ms=duration
                )
            else:
                duration = (datetime.now() - start).total_seconds() * 1000
                return HealthCheckResult(
                    name=f"account_{account.id}",
                    status=False,
                    details="Not authorized",
                    duration_ms=duration
                )
        
        except AuthKeyUnregisteredError:
            duration = (datetime.now() - start).total_seconds() * 1000
            return HealthCheckResult(
                name=f"account_{account.id}",
                status=False,
                details="Auth key unregistered (session revoked)",
                duration_ms=duration
            )
        
        finally:
            await client.disconnect()
    
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"[health] account {account.id} check failed: {e}")
        return HealthCheckResult(
            name=f"account_{account.id}",
            status=False,
            details=f"Error: {e}",
            duration_ms=duration
        )


async def run_health_check() -> SystemHealth:
    """
    Запустить полную проверку здоровья системы.
    
    Returns:
        SystemHealth с результатами всех проверок
    """
    checks = []
    
    # Параллельно запускаем независимые проверки
    results = await asyncio.gather(
        check_database(),
        check_sessions_folder(),
        check_accounts_consistency(),
        check_telegram_api(),
        return_exceptions=True
    )
    
    for result in results:
        if isinstance(result, Exception):
            checks.append(HealthCheckResult(
                name="unknown",
                status=False,
                details=f"Check failed: {result}",
                duration_ms=0
            ))
        else:
            checks.append(result)
    
    overall = all(c.status for c in checks)
    
    return SystemHealth(
        overall=overall,
        checks=checks,
        timestamp=datetime.now()
    )


def format_health_report(health: SystemHealth) -> str:
    """
    Форматирование отчёта о здоровье.
    
    Args:
        health: Результат проверки
        
    Returns:
        Форматированная строка для сообщения
    """
    status_emoji = "✅" if health.overall else "❌"
    
    lines = [
        f"{status_emoji} **Статус системы: {'OK' if health.overall else 'ПРОБЛЕМЫ'}**",
        f"📅 {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    for check in health.checks:
        emoji = "✅" if check.status else "❌"
        lines.append(f"{emoji} **{check.name}**: {check.details} ({check.duration_ms:.0f}ms)")
    
    return "\n".join(lines)
