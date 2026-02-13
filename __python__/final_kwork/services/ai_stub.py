"""
Сервис анализа рисков (эвристика).

Простая эвристика для оценки риска выдачи аккаунта.
Может быть заменена на LLM в будущем.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Константы для расчёта риска
RISK_HIGH_THRESHOLD = 0.7
RISK_MEDIUM_THRESHOLD = 0.3
MAX_REVOKED_FOR_HIGH_RISK = 3
MAX_REVOKED_FOR_MEDIUM_RISK = 1
RECENT_REQUESTS_WINDOW_HOURS = 24
MAX_RECENT_REQUESTS = 5


async def analyze_request(
    user_tg_id: int, 
    username: Optional[str], 
    history: List[Dict[str, Any]]
) -> float:
    """
    Анализ запроса на выдачу аккаунта.
    
    Args:
        user_tg_id: Telegram ID пользователя
        username: Username пользователя
        history: История предыдущих запросов пользователя
    
    Returns:
        risk_score от 0.0 (безопасно) до 1.0 (подозрительно)
    """
    if not history:
        return 0.1  # Новый пользователь - низкий риск
    
    risk_score = 0.0
    
    # 1. Подсчёт отозванных аккаунтов
    revoked_count = sum(1 for h in history if h.get("status") == "revoked")
    if revoked_count >= MAX_REVOKED_FOR_HIGH_RISK:
        risk_score += 0.5
    elif revoked_count >= MAX_REVOKED_FOR_MEDIUM_RISK:
        risk_score += 0.2
    
    # 2. Частота запросов за последние 24 часа
    now = datetime.utcnow()
    window_start = now - timedelta(hours=RECENT_REQUESTS_WINDOW_HOURS)
    recent_requests = 0
    
    for h in history:
        requested_at = h.get("requested_at")
        if requested_at:
            if isinstance(requested_at, str):
                try:
                    requested_at = datetime.fromisoformat(requested_at.replace("Z", "+00:00"))
                except ValueError:
                    continue
            if isinstance(requested_at, datetime) and requested_at >= window_start:
                recent_requests += 1
    
    if recent_requests >= MAX_RECENT_REQUESTS:
        risk_score += 0.3
    elif recent_requests >= 3:
        risk_score += 0.1
    
    # 3. Наличие отклонённых заявок
    rejected_count = sum(1 for h in history if h.get("status") == "rejected")
    if rejected_count >= 2:
        risk_score += 0.2
    
    # Нормализуем до [0, 1]
    return min(1.0, max(0.0, risk_score))
