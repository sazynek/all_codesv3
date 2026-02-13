"""
Настройка логирования.
"""
import logging
import sys
from typing import Optional


def setup_logging(level: Optional[int] = None) -> None:
    """
    Настройка корневого логгера.
    
    Args:
        level: Уровень логирования. Если None - берётся из config.LOG_LEVEL
    """
    from config import settings
    
    if level is None:
        level = getattr(logging, settings.log_level, logging.INFO)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
    
    # Приглушаем слишком verbose библиотеки
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
