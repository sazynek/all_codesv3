"""
Обработчики команд менеджера с современным UI.

Поддерживает как команды (fallback), так и inline-кнопки.
Совместимость с Telethon 2.0.
"""
import logging

from services.telethon_adapter import TelegramClient, events, Button

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.constants import ISSUE_STATUS_EMOJI, ISSUE_STATUS_NAMES
from bot.decorators import safe_edit
from db.session import get_session
from db.models import Issue, IssueStatus, Account
from services.telethon_workers import start_code_listener, stop_code_listener
from services import issues_service, security_service, ai_stub
from bot.keyboards import (
    CB,
    main_menu_manager,
    main_menu_admin,
    admin_issue_card,
    manager_request_sent,
    manager_limit_reached,
    manager_my_accounts_list,
    manager_my_accounts_empty,
    manager_history_list,
    manager_history_empty,
    manager_help,
    manager_code_timeout,
    manager_code_received,
)
from config import settings

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом."""
    return user_id in settings.admin_ids_list


def register_manager_handlers(client: TelegramClient) -> None:
    """Регистрация обработчиков для менеджеров."""
    
    # ================================================================
    # КОМАНДА /start - ГЛАВНОЕ МЕНЮ
    # ================================================================
    
    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def cmd_start(event):
        """Приветствие с меню по роли."""
        sender = await event.get_sender()
        user_id = sender.id
        
        if is_admin(user_id):
            text = (
                "👋 **Привет!**\n\n"
                "🔐 Вы администратор системы.\n"
                "Выберите действие:"
            )
            buttons = main_menu_admin()
        else:
            text = (
                "👋 **Привет!**\n\n"
                "Я помогу получить рабочий аккаунт Telegram.\n"
                "Выбери действие:"
            )
            buttons = main_menu_manager()
        
        await event.respond(text, buttons=buttons)
    
    # ================================================================
    # НАВИГАЦИЯ ПО МЕНЮ (callback)
    # ================================================================
    
    @client.on(events.CallbackQuery(pattern=rb"^(nav:main|mgr:menu)$"))
    @safe_edit
    async def cb_nav_main(event):
        """Возврат в главное меню."""
        user_id = event.sender_id
        
        if is_admin(user_id):
            text = "🏠 **Главное меню**\n\nВыберите действие:"
            buttons = main_menu_admin()
        else:
            text = (
                "👋 **Привет!**\n\n"
                "Я помогу получить рабочий аккаунт Telegram.\n"
                "Выбери действие:"
            )
            buttons = main_menu_manager()
        
        await event.edit(text, buttons=buttons)
    
    # ================================================================
    # ЗАПРОС АККАУНТА
    # ================================================================
    
    @client.on(events.NewMessage(pattern=r"^/get_account$"))
    async def cmd_get_account(event):
        """Запрос аккаунта (команда)."""
        await process_get_account(event, client, is_callback=False)
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:get(_account)?$"))
    @safe_edit
    async def cb_get_account(event):
        """Запрос аккаунта (кнопка)."""
        await process_get_account(event, client, is_callback=True)

    # ================================================================
    # ПОВТОРНОЕ ОЖИДАНИЕ КОДА (когда менеджер заново инициировал вход)
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^mgr:wait_code_again$"))
    @safe_edit
    async def cb_wait_code_again(event):
        """Перезапустить ожидание кода для последнего выданного аккаунта."""
        sender = await event.get_sender()
        tg_id = sender.id
        username = sender.username
        full_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

        await event.answer("⏳ Перезапускаю ожидание кода...")
        await event.edit(
            "⏳ Перезапускаю ожидание кода...\n\n"
            "Если вы заново нажали *Войти* в Telegram — я поймаю новый код.",
            buttons=manager_code_timeout(),
        )

        async with get_session() as session:
            user = await issues_service.get_or_create_user(session, tg_id, username, full_name)

            # Берём последнюю одобренную заявку менеджера (аккаунт уже закреплён)
            stmt = (
                select(Issue)
                .where(
                    Issue.user_id == user.id,
                    Issue.status == IssueStatus.APPROVED,
                )
                .options(
                    selectinload(Issue.account).selectinload(Account.proxy),
                    selectinload(Issue.user),
                )
                .order_by(Issue.approved_at.desc())
                .limit(1)
            )

            res = await session.execute(stmt)
            issue = res.scalar_one_or_none()

            if not issue or not issue.account:
                await event.edit(
                    "⚠️ У вас нет выданного аккаунта.\n"
                    "Сначала отправьте заявку на аккаунт.",
                    buttons=main_menu_manager(),
                )
                return

            account = issue.account
            if not account.session_path:
                await event.edit(
                    "⚠️ У этого аккаунта нет .session файла.\n"
                    "Сообщите администратору.",
                    buttons=main_menu_manager(),
                )
                return

            proxy_dict = None
            if getattr(account, "proxy", None) and account.proxy.is_active:
                try:
                    proxy_dict = account.proxy.to_telethon_dict()
                except Exception:
                    proxy_dict = None

            # Колбэки (как в админке, но без привязки к админ-сообщению)
            async def _on_connected(account_id: int, manager_tg_id: int, phone: str, tg_username: str, is_premium: bool):
                try:
                    await client.send_message(
                        manager_tg_id,
                        f"📞 Обновлён номер аккаунта: `{phone}`",
                    )
                except Exception:
                    pass

            async def _on_code(account_id: int, manager_tg_id: int, code: str):
                # Сохраняем код в issue (чтобы выдача считалась «активной»)
                async with get_session() as s2:
                    iss = await issues_service.get_issue_by_id(s2, issue.id)
                    if iss and iss.status == IssueStatus.APPROVED:
                        await issues_service.set_confirmation_code(s2, iss, code)

                try:
                    await client.send_message(
                        manager_tg_id,
                        f"🔐 Код подтверждения: `{code}`\n\n"
                        "Если вход не удался — нажмите *Код ещё раз*.",
                        buttons=manager_code_received(),
                    )
                except Exception:
                    pass

            async def _on_timeout(account_id: int, manager_tg_id: int):
                try:
                    await client.send_message(
                        manager_tg_id,
                        "⌛️ Время ожидания кода истекло.\n"
                        "Если вы снова пытаетесь войти — нажмите *Ещё раз*.",
                        buttons=manager_code_timeout(),
                    )
                except Exception:
                    pass

            async def _on_error(account_id: int, manager_tg_id: int, error_text: str):
                try:
                    await client.send_message(manager_tg_id, f"⚠️ {error_text}")
                except Exception:
                    pass

        # Перезапускаем слушатель вне DB-сессии
        try:
            await stop_code_listener(account.id)
        except Exception:
            pass

        try:
            await start_code_listener(
                account_id=account.id,
                session_path=account.session_path,
                manager_tg_id=tg_id,
                on_code_received=_on_code,
                on_timeout=_on_timeout,
                on_error=_on_error,
                bot_client=client,
                proxy=proxy_dict,
                api_id=account.api_id,
                api_hash=account.api_hash,
                account_phone=account.phone,
                device_model=account.device_model,
                system_version=account.system_version,
                app_version=account.app_version,
                lang_code=account.lang_code,
                system_lang_code=account.system_lang_code,
                on_connected=_on_connected,
            )
        except Exception as e:
            logger.error(f"Failed to restart code listener for manager {tg_id}: {e}")
            await event.edit(
                "⚠️ Не удалось запустить ожидание кода.\n"
                "Сообщите администратору.",
                buttons=main_menu_manager(),
            )
            return

        await event.edit(
            "✅ Ожидание кода запущено.\n"
            "Когда код придёт — я отправлю его сюда.",
            buttons=manager_code_timeout(),
        )
    
    async def process_get_account(event, client, is_callback: bool):
        """Общая логика запроса аккаунта."""
        sender = await event.get_sender()
        tg_id = sender.id
        username = sender.username
        full_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        
        async with get_session() as session:
            # Получаем/создаём пользователя
            user = await issues_service.get_or_create_user(
                session, tg_id, username, full_name
            )
            
            # Проверка лимитов
            is_valid, error_msg = await security_service.validate_request(session, user.id)
            if not is_valid:
                text = f"⚠️ **Лимит достигнут**\n\n{error_msg}"
                if is_callback:
                    await event.edit(text, buttons=manager_limit_reached())
                else:
                    await event.respond(text, buttons=manager_limit_reached())
                return
            
            # AI-анализ
            history = await issues_service.get_user_history(session, user.id)
            risk_score = await ai_stub.analyze_request(tg_id, username, history)
            
            # Создаём заявку
            issue = await issues_service.create_issue(
                session, user, ip_address=None, risk_score=risk_score
            )
            
            # Ответ менеджеру
            response_text = (
                "✅ **Заявка отправлена!**\n\n"
                "Ожидай подтверждения от администратора.\n"
                "Обычно это занимает пару минут ⏳"
            )
            
            if is_callback:
                await event.edit(response_text, buttons=manager_request_sent())
            else:
                await event.respond(response_text, buttons=manager_request_sent())
            
            # Уведомляем админов
            if history:
                approved_count = sum(1 for h in history if h.get("status") == "approved")
                history_text = f"📊 Заявок ранее: {len(history)}\n✅ Выдано аккаунтов: {approved_count}"
            else:
                history_text = "🆕 Первая заявка"
            
            admin_text = (
                f"📩 **Новая заявка #{issue.id}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 **Пользователь**\n"
                f"   ├ Username: @{username or 'нет'}\n"
                f"   ├ ID: `{tg_id}`\n"
                f"   └ Имя: {full_name or 'не указано'}\n\n"
                f"{history_text}"
            )
            
            for admin_id in settings.admin_ids_list:
                try:
                    await client.send_message(
                        admin_id,
                        admin_text,
                        buttons=admin_issue_card(issue.id)
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # ================================================================
    # МОИ АККАУНТЫ
    # ================================================================
    
    @client.on(events.NewMessage(pattern=r"^/my_accounts$"))
    async def cmd_my_accounts(event):
        """Мои аккаунты (команда)."""
        await process_my_accounts(event, is_callback=False)
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:my(_accounts)?$"))
    @safe_edit
    async def cb_my_accounts(event):
        """Мои аккаунты (кнопка)."""
        await process_my_accounts(event, is_callback=True)
    
    async def process_my_accounts(event, is_callback: bool):
        """Общая логика просмотра аккаунтов."""
        sender = await event.get_sender()
        tg_id = sender.id
        
        async with get_session() as session:
            user = await issues_service.get_or_create_user(session, tg_id)
            active = await issues_service.get_active_issues(session)
            my_active = [i for i in active if i.user_id == user.id]
            
            # Проверяем лимит
            can_request_more = len(my_active) < settings.max_accounts_per_manager
            
            if not my_active:
                text = (
                    "📭 **Нет активных аккаунтов**\n\n"
                    "Запроси аккаунт, чтобы начать работу."
                )
                buttons = manager_my_accounts_empty()
            else:
                lines = [f"📱 **Твои аккаунты** ({len(my_active)}/{settings.max_accounts_per_manager})\n"]
                for issue in my_active:
                    acc = issue.account
                    if acc:
                        premium = "⭐" if acc.is_premium else ""
                        lines.append(f"• `{acc.phone}` {premium}")
                
                lines.append("\n💡 Когда закончишь — сообщи админу для отзыва.")
                text = "\n".join(lines)
                buttons = manager_my_accounts_list(my_active, can_request_more)
            
            if is_callback:
                await event.edit(text, buttons=buttons)
            else:
                await event.respond(text, buttons=buttons)
    
    # ================================================================
    # ИСТОРИЯ ВЫДАЧ
    # ================================================================
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:history:(\d+)$"))
    @safe_edit
    async def cb_history(event):
        """История выдач менеджера."""
        page = int(event.pattern_match.group(1).decode())
        await process_history(event, page)
    
    async def process_history(event, page: int = 0):
        """Показать историю выдач менеджера."""
        sender = await event.get_sender()
        tg_id = sender.id
        
        async with get_session() as session:
            user = await issues_service.get_or_create_user(session, tg_id)
            all_issues = await issues_service.get_all_issues(session, limit=100)
            my_issues = [i for i in all_issues if i.user_id == user.id]
            
            if not my_issues:
                text = (
                    "📭 **История пуста**\n\n"
                    "Ты ещё не запрашивал аккаунты."
                )
                await event.edit(text, buttons=manager_history_empty())
                return
            
            # Пагинация
            per_page = 5
            start = page * per_page
            end = start + per_page
            page_issues = my_issues[start:end]
            total_pages = max(1, (len(my_issues) + per_page - 1) // per_page)
            
            lines = [f"📜 **История выдач** (стр. {page + 1}/{total_pages})\n"]
            
            for issue in page_issues:
                status_val = issue.status.value if hasattr(issue.status, 'value') else str(issue.status)
                emoji = ISSUE_STATUS_EMOJI.get(status_val, "⚪")
                date = issue.requested_at.strftime("%d.%m") if issue.requested_at else "?"
                phone = issue.account.phone if issue.account else "—"
                status_text = ISSUE_STATUS_NAMES.get(status_val, status_val).lower()
                lines.append(f"`{date}` • {phone} — {emoji} {status_text}")
            
            text = "\n".join(lines)
            await event.edit(text, buttons=manager_history_list(my_issues, page, per_page))
    
    # ================================================================
    # СТАТУС ЗАЯВКИ
    # ================================================================
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:status$"))
    @safe_edit
    async def cb_status(event):
        """Статус последней заявки."""
        sender = await event.get_sender()
        tg_id = sender.id
        
        async with get_session() as session:
            user = await issues_service.get_or_create_user(session, tg_id)
            pending = await issues_service.get_pending_by_user(session, user.id)
            
            if not pending:
                text = "📭 **Нет активных заявок**\n\nТы можешь запросить новый аккаунт."
                await event.edit(text, buttons=manager_my_accounts_empty())
                return
            
            issue = pending[0]
            text = (
                f"⏳ **Заявка #{issue.id}**\n\n"
                f"Статус: ожидает подтверждения\n"
                f"Создана: {issue.requested_at.strftime('%d.%m.%Y %H:%M') if issue.requested_at else '?'}"
            )
            await event.edit(text, buttons=manager_request_sent())
    
    # ================================================================
    # СВЯЗАТЬСЯ С АДМИНОМ
    # ================================================================
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:contact_admin$"))
    @safe_edit
    async def cb_contact_admin(event):
        """Информация о связи с админом."""
        text = (
            "📞 **Связь с администратором**\n\n"
            "Напиши в личные сообщения одному из админов.\n"
            "Они помогут решить проблему."
        )
        await event.edit(text, buttons=[[Button.inline("⬅️ В меню", data=CB.MGR_MENU)]])
    
    # ================================================================
    # ПОМОЩЬ
    # ================================================================
    
    @client.on(events.NewMessage(pattern=r"^/help$"))
    async def cmd_help(event):
        """Помощь (команда)."""
        await process_help(event, is_callback=False)
    
    @client.on(events.CallbackQuery(pattern=rb"^mgr:help$"))
    @safe_edit
    async def cb_help(event):
        """Помощь (кнопка)."""
        await process_help(event, is_callback=True)
    
    async def process_help(event, is_callback: bool):
        """Общая логика помощи."""
        text = (
            "❓ **Справка**\n\n"
            "**Как получить аккаунт:**\n"
            "1. Нажми «Получить аккаунт»\n"
            "2. Дождись одобрения админа\n"
            "3. Получи номер и код\n"
            "4. Войди в Telegram\n\n"
            f"**Лимит:** {settings.max_accounts_per_manager} аккаунта одновременно"
        )
        
        if is_callback:
            await event.edit(text, buttons=manager_help())
        else:
            await event.respond(text, buttons=manager_help())
    
    # ================================================================
    # УТИЛИТЫ
    # ================================================================
    
    @client.on(events.CallbackQuery(pattern=rb"^noop$"))
    async def cb_noop(event):
        """Пустой callback (для информационных кнопок)."""
        await event.answer()
    
    @client.on(events.CallbackQuery(pattern=rb"^close$"))
    async def cb_close(event):
        """Закрыть сообщение."""
        await event.delete()
