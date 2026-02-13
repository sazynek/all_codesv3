"""
Декораторы для handlers.

Включает:
- admin_only: проверка прав админа
- safe_edit: безопасное редактирование сообщений (игнорирует MessageNotModifiedError)
- handle_errors: обработка ошибок с уведомлением пользователя
"""
import functools
import logging
from typing import Callable, TypeVar, ParamSpec

from telethon.errors import MessageNotModifiedError, MessageIdInvalidError

from config import settings

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def safe_edit(func: Callable[P, T]) -> Callable[P, T]:
    """
    Декоратор: безопасное редактирование сообщений.
    
    Игнорирует MessageNotModifiedError (когда текст/кнопки не изменились)
    и MessageIdInvalidError (когда сообщение уже удалено).
    
    Остальные ошибки логируются и пробрасываются.
    
    Использование:
        @safe_edit
        async def cb_some_menu(event):
            await event.edit("Text", buttons=...)
    """
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        try:
            return await func(event, *args, **kwargs)
        except MessageNotModifiedError:
            # Сообщение уже содержит этот текст - игнорируем
            logger.debug(f"MessageNotModifiedError ignored in {func.__name__}")
            # Отвечаем на callback чтобы убрать "часики"
            if hasattr(event, 'answer'):
                try:
                    await event.answer()
                except Exception:
                    pass
            return None
        except MessageIdInvalidError:
            # Сообщение удалено - игнорируем
            logger.debug(f"MessageIdInvalidError ignored in {func.__name__}")
            return None
    
    return wrapper


def admin_only(func: Callable[P, T]) -> Callable[P, T]:
    """
    Декоратор: только для админов.
    Для NewMessage и CallbackQuery events.
    
    Также игнорирует MessageNotModifiedError.
    """
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        
        if user_id not in settings.admin_ids_list:
            # Для callback — показываем alert
            if hasattr(event, 'answer'):
                await event.answer("⛔ Нет доступа", alert=True)
            return None
        
        try:
            return await func(event, *args, **kwargs)
        except MessageNotModifiedError:
            # Игнорируем - сообщение уже содержит этот текст
            logger.debug(f"MessageNotModifiedError ignored in {func.__name__}")
            if hasattr(event, 'answer'):
                try:
                    await event.answer()
                except Exception:
                    pass
            return None
        except MessageIdInvalidError:
            # Сообщение удалено - игнорируем
            logger.debug(f"MessageIdInvalidError ignored in {func.__name__}")
            return None
    
    return wrapper


def log_handler(action: str) -> Callable:
    """
    Декоратор: логирование handler с контекстом.
    
    Usage:
        @log_handler("approve_issue")
        async def cb_approve(event):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id
            logger.info(f"[{action}] user_id={user_id} started")
            
            try:
                result = await func(event, *args, **kwargs)
                logger.info(f"[{action}] user_id={user_id} completed")
                return result
            except Exception as e:
                logger.exception(f"[{action}] user_id={user_id} error: {e}")
                raise
        
        return wrapper
    return decorator


def handle_errors(user_message: str = "❌ Произошла ошибка. Попробуйте позже."):
    """
    Декоратор: обработка ошибок с отправкой сообщения пользователю.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            try:
                return await func(event, *args, **kwargs)
            except Exception as e:
                logger.exception(f"Handler error: {e}")
                
                try:
                    if hasattr(event, 'answer'):
                        await event.answer(user_message[:200], alert=True)
                    else:
                        await event.respond(user_message)
                except Exception:
                    pass
                
                return None
        
        return wrapper
    return decorator
