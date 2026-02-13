"""
Обработчики команд администратора с современным UI.

Поддерживает inline-кнопки как основной интерфейс,
команды работают как fallback.
Совместимость с Telethon 2.0.
"""

import logging
import os
import shutil
from typing import Optional, Dict, Any

from services.telethon_adapter import TelegramClient, events, Button

from bot.constants import (
    STATUS_EMOJI_MAP,
    ACCOUNT_STATUS_NAMES,
    ISSUE_STATUS_EMOJI,
    ISSUE_STATUS_NAMES,
)
from bot.decorators import admin_only
from bot.keyboards import (
    main_menu_admin,
    admin_import_menu,
    admin_import_result,
    admin_accounts_filter,
    admin_accounts_list,
    admin_account_detail,
    admin_active_issues_list,
    admin_history_list,
    admin_issue_processed,
    confirm_revoke,
    confirm_delete_account,
    issue_detail_buttons,
    back_button,
    manager_account_issued,
    manager_code_received,
    manager_code_timeout,
    admin_proxies_menu,
    admin_proxies_list,
    admin_proxy_detail,
    confirm_delete_proxy,
    admin_add_proxy_result,
    admin_managers_list,
    admin_manager_detail,
    confirm_revoke_all,
    CB,
)
from config import settings
from db.models import AccountStatus, IssueStatus, StorageType
from db.session import get_session
from services import (
    accounts_service,
    issues_service,
    session_import_service,
    tdata_converter,
    batch_import_service,
)
from services.telethon_workers import (
    start_code_listener,
    stop_code_listener,
    reset_other_sessions,
)
from services.stats_service import get_system_stats, format_stats_message
from services.health_service import run_health_check, format_health_report
from services import proxy_service

logger = logging.getLogger(__name__)

# Состояние пользователей для пошагового импорта
_user_states: Dict[int, Dict[str, Any]] = {}


def register_admin_handlers(client: TelegramClient) -> None:
    """Регистрация обработчиков для админов."""

    # ================================================================
    # НАВИГАЦИЯ ПО МЕНЮ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^nav:import$"))
    @admin_only
    async def cb_nav_import(event):
        """Экран импорта аккаунтов."""
        text = "📥 **Импорт аккаунтов**\n\n" "Выберите тип файла для импорта:"
        await event.edit(text, buttons=admin_import_menu())

    @client.on(events.CallbackQuery(pattern=rb"^nav:accounts$"))
    @admin_only
    async def cb_nav_accounts(event):
        """Экран фильтров аккаунтов."""
        async with get_session() as session:
            accounts = await accounts_service.get_all_accounts(session)

        # Подсчёт по статусам
        counts = {"free": 0, "assigned": 0, "disabled": 0, "needs_conversion": 0}
        for acc in accounts:
            status = (
                acc.status.value if hasattr(acc.status, "value") else str(acc.status)
            )
            if status in counts:
                counts[status] += 1

        text = (
            f"🗂 **Аккаунты** (всего: {len(accounts)})\n\n"
            f"🟢 Свободные:     {counts['free']}\n"
            f"🔵 Выданные:      {counts['assigned']}\n"
            f"🔴 Невалид:       {counts['disabled']}\n"
            f"🟡 Конвертация:   {counts['needs_conversion']}\n\n"
            "Выберите фильтр:"
        )
        await event.edit(text, buttons=admin_accounts_filter())

    @client.on(events.CallbackQuery(pattern=rb"^nav:active$"))
    @admin_only
    async def cb_nav_active(event):
        """Экран активных выдач."""
        await show_active_issues(event, page=0)

    @client.on(events.CallbackQuery(pattern=rb"^nav:history$"))
    @admin_only
    async def cb_nav_history(event):
        """Экран истории заявок."""
        await show_history(event, page=0)

    @client.on(events.CallbackQuery(pattern=rb"^nav:stats$"))
    @admin_only
    async def cb_nav_stats(event):
        """Экран статистики."""
        async with get_session() as session:
            stats = await get_system_stats(session)

        text = format_stats_message(stats)
        await event.edit(text, buttons=back_button("nav:main"))

    @client.on(events.CallbackQuery(pattern=rb"^nav:settings$"))
    @admin_only
    async def cb_nav_settings(event):
        """Экран настроек."""
        text = (
            "⚙️ **Настройки**\n\n"
            f"📁 Папка сессий: `{settings.sessions_dir}`\n"
            f"⏱ Таймаут кода: {settings.code_wait_timeout} сек\n\n"
            f"**Лимиты:**\n"
            f"👥 Аккаунтов на менеджера: {settings.max_accounts_per_manager}\n"
            f"⏳ Cooldown между запросами: {settings.request_cooldown_seconds} сек\n\n"
            f"👨‍💼 Админы: {len(settings.admin_ids_list)}\n\n"
            "💡 Настройки изменяются в файле `.env.example`"
        )
        await event.edit(text, buttons=back_button("nav:main"))

    # ================================================================
    # ИМПОРТ АККАУНТОВ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^import:session$"))
    @admin_only
    async def cb_import_session(event):
        """Начало импорта .session файлов."""
        _user_states[event.sender_id] = {"mode": "import_session"}
        text = (
            "📄 **Импорт Session**\n\n"
            "Отправьте `.session` файл или ZIP с `.session` файлами.\n"
            "📏 Макс: 100 MB"
        )
        await event.edit(text, buttons=back_button("nav:import"))

    @client.on(events.CallbackQuery(pattern=rb"^import:tdata$"))
    @admin_only
    async def cb_import_tdata(event):
        """Начало импорта tdata."""
        _user_states[event.sender_id] = {"mode": "import_tdata"}
        text = (
            "📦 **Импорт TData**\n\n"
            "Отправьте ZIP с папкой `tdata`.\n"
            "📏 Макс: 100 MB"
        )
        await event.edit(text, buttons=back_button("nav:import"))

    @client.on(
        events.NewMessage(
            func=lambda e: e.document and e.sender_id in settings.admin_ids_list
        )
    )
    async def handle_document(event):
        """Обработка загруженных документов."""
        doc = event.document
        filename = _get_document_filename(doc)

        logger.info(f"Document received: {filename}, sender={event.sender_id}")

        if not filename:
            logger.warning("No filename in document")
            return

        user_state = _user_states.get(event.sender_id, {})
        mode = user_state.get("mode")

        filename_lower = filename.lower()

        # Проверка размера
        max_size = batch_import_service.MAX_ZIP_SIZE

        if doc.size > max_size:
            await event.respond(
                f"❌ Файл слишком большой\n" f"Максимум: {max_size // 1024 // 1024} MB",
                buttons=admin_import_result(False),
            )
            return

        # Импорт сессий через ZIP
        if mode == "import_session" and filename_lower.endswith(".zip"):
            await _handle_batch_sessions_zip(event, client, filename)
        # Импорт одиночного .session файла
        elif mode == "import_session" and filename_lower.endswith(".session"):
            await _handle_session_file(event, client, filename)
        # Импорт tdata через ZIP
        elif mode == "import_tdata" and filename_lower.endswith(".zip"):
            await _handle_tdata_import(event, filename)
        elif filename_lower.endswith(".zip"):
            # Автоопределение - пробуем как архив с сессиями
            await _handle_batch_sessions_zip(event, client, filename)
        elif filename_lower.endswith(".session"):
            # Автоопределение - одиночный .session файл
            await _handle_session_file(event, client, filename)
        elif filename_lower.endswith(".7z") or filename_lower.endswith(".rar"):
            await event.respond(
                f"⚠️ Формат {filename_lower[-4:].upper()} не поддерживается.\n"
                "Перепакуйте в ZIP.",
                buttons=admin_import_result(False),
            )

        # Сбрасываем состояние
        _user_states.pop(event.sender_id, None)

    # ================================================================
    # ФИЛЬТРЫ И СПИСКИ АККАУНТОВ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^filter:(\w+):(\d+)$"))
    @admin_only
    async def cb_filter_accounts(event):
        """Фильтр аккаунтов с пагинацией."""
        match = event.pattern_match
        filter_type = match.group(1).decode()
        page = int(match.group(2).decode())

        async with get_session() as session:
            all_accounts = await accounts_service.get_all_accounts(session)

        # Фильтруем
        if filter_type == "all":
            accounts = all_accounts
        else:
            accounts = [
                a
                for a in all_accounts
                if (a.status.value if hasattr(a.status, "value") else str(a.status))
                == filter_type
            ]

        if not accounts:
            status_names = {
                "free": "свободных",
                "assigned": "выданных",
                "disabled": "отключённых",
                "needs_conversion": "для конвертации",
            }
            name = status_names.get(filter_type, "")
            text = f"📭 Нет {name} аккаунтов"
            await event.edit(text, buttons=back_button("nav:accounts"))
            return

        text = f"🗂 **Аккаунты** ({len(accounts)} шт.)\n\nВыберите аккаунт:"
        await event.edit(text, buttons=admin_accounts_list(accounts, filter_type, page))

    # ================================================================
    # ДЕТАЛИ АККАУНТА
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^acc:detail:(\d+)$"))
    @admin_only
    async def cb_account_detail(event):
        """Детали аккаунта."""
        account_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            account = await accounts_service.get_account_by_id(session, account_id)

            if not account:
                await event.answer("Аккаунт не найден", alert=True)
                return

            # Получаем владельца если аккаунт выдан
            owner_info = None
            if account.status == AccountStatus.ASSIGNED:
                owner_info = await issues_service.get_account_owner(session, account_id)

        status_value = (
            account.status.value
            if hasattr(account.status, "value")
            else str(account.status)
        )
        status_emoji = STATUS_EMOJI_MAP.get(status_value, "⚪")
        status_name = ACCOUNT_STATUS_NAMES.get(status_value, status_value)
        storage = (
            "📦 TData" if account.storage_type == StorageType.TDATA else "📄 Session"
        )
        premium_status = "⭐ Да" if account.is_premium else "❌ Нет"

        # Отображение API credentials
        if account.api_id:
            api_display = f"🔑 API: `{str(account.api_id)[:8]}...` (📦 аккаунта)\n"
        else:
            api_display = f"🔑 API: (⚙️ из .env.example)\n"

        text = (
            f"📋 **Аккаунт #{account.id}**\n\n"
            f"📞 Телефон: `{account.phone or 'не указан'}`\n"
            f"👤 Username: @{account.username or 'нет'}\n"
            f"🆔 TG ID: `{account.tg_user_id or 'нет'}`\n"
            f"{status_emoji} Статус: {status_name}\n"
            f"{storage}\n"
            f"{api_display}"
            f"💎 Premium: {premium_status}\n"
        )

        # Показываем владельца если аккаунт выдан
        if owner_info:
            owner_username = (
                f"@{owner_info['username']}" if owner_info.get("username") else ""
            )
            owner_tg_id = owner_info.get("tg_id", "?")
            issued_at = owner_info.get("issued_at")
            issued_str = issued_at.strftime("%d.%m.%Y %H:%M") if issued_at else "?"
            text += (
                f"\n👤 **Владелец:** {owner_username} (`{owner_tg_id}`)\n"
                f"📅 Выдан: {issued_str}\n"
                f"📋 Заявка: #{owner_info.get('issue_id')}"
            )

        if account.error_text:
            text += f"\n\n⚠️ Ошибка: {account.error_text}"

        can_convert = (
            account.storage_type == StorageType.TDATA and not account.session_path
        )
        await event.edit(text, buttons=admin_account_detail(account, can_convert))

    @client.on(events.CallbackQuery(pattern=rb"^acc:check:(\d+)$"))
    @admin_only
    async def cb_account_check(event):
        """Проверка валидности аккаунта."""
        account_id = int(event.pattern_match.group(1).decode())

        await event.answer("⏳ Проверяю...", alert=False)

        async with get_session() as session:
            account = await accounts_service.get_account_by_id(session, account_id)

            if not account or not account.session_path:
                await event.answer("Нет session файла", alert=True)
                return

            # Используем api_id/api_hash аккаунта и skip_connect чтобы не убить сессию
            validation = await session_import_service.validate_session(
                account.session_path,
                api_id=account.api_id,
                api_hash=account.api_hash,
                skip_connect=True,  # НЕ подключаемся - только проверяем файлы
            )

            if validation.success:
                # Обновляем данные
                if validation.username != account.username:
                    account.username = validation.username
                if validation.is_premium != account.is_premium:
                    account.is_premium = validation.is_premium
                account.error_text = None
                await session.flush()

                text = f"✅ Аккаунт #{account_id} валиден!"
            else:
                account.status = AccountStatus.DISABLED
                account.error_text = validation.error
                await session.flush()

                text = f"❌ Аккаунт #{account_id}: {validation.error}"

        await event.answer(text, alert=True)

    @client.on(events.CallbackQuery(pattern=rb"^acc:delete:(\d+)$"))
    @admin_only
    async def cb_account_delete(event):
        """Запрос подтверждения удаления."""
        account_id = int(event.pattern_match.group(1).decode())

        text = f"⚠️ **Удалить аккаунт #{account_id}?**\n\nЭто действие необратимо!"
        await event.edit(text, buttons=confirm_delete_account(account_id))

    @client.on(events.CallbackQuery(pattern=rb"^acc:confirm_delete:(\d+)$"))
    @admin_only
    async def cb_account_confirm_delete(event):
        """Подтверждение удаления аккаунта."""
        account_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            account = await accounts_service.get_account_by_id(session, account_id)

            if not account:
                await event.answer("Аккаунт не найден", alert=True)
                return

            if account.status == AccountStatus.ASSIGNED:
                await event.answer("Сначала отзовите аккаунт!", alert=True)
                return

            # Удаляем файлы
            await _cleanup_account_files(account)
            await session.delete(account)

            identifier = account.phone or account.tg_user_id or "unknown"

        text = f"✅ Аккаунт #{account_id} ({identifier}) удалён"
        await event.edit(text, buttons=back_button("nav:accounts"))
        logger.info(f"Account #{account_id} deleted by admin {event.sender_id}")

    @client.on(events.CallbackQuery(pattern=rb"^acc:convert:(\d+)$"))
    @admin_only
    async def cb_account_convert(event):
        """Конвертация tdata в session."""
        account_id = int(event.pattern_match.group(1).decode())

        await event.answer("⏳ Конвертирую...", alert=False)

        async with get_session() as session:
            account = await accounts_service.get_account_by_id(session, account_id)

            if not account or not account.tdata_path:
                await event.answer("TData не найден", alert=True)
                return

            success, message = await tdata_converter.convert_account_tdata(
                session, account
            )

        await event.answer(message[:200], alert=True)

    # ================================================================
    # АКТИВНЫЕ ВЫДАЧИ
    # ================================================================

    async def show_active_issues(event, page: int = 0):
        """Показать активные выдачи."""
        async with get_session() as session:
            issues = await issues_service.get_active_issues(session)

        if not issues:
            text = "📭 **Нет активных выдач**"
            await event.edit(text, buttons=back_button("nav:main"))
            return

        text = f"✅ **Активные выдачи** ({len(issues)} шт.)"
        await event.edit(text, buttons=admin_active_issues_list(issues, page))

    @client.on(events.CallbackQuery(pattern=rb"^page:active:(\d+)$"))
    @admin_only
    async def cb_page_active(event):
        """Пагинация активных выдач."""
        page = int(event.pattern_match.group(1).decode())
        await show_active_issues(event, page)

    # ================================================================
    # ИСТОРИЯ ЗАЯВОК
    # ================================================================

    async def show_history(event, page: int = 0):
        """Показать историю заявок."""
        async with get_session() as session:
            issues = await issues_service.get_all_issues(session, limit=100)

        if not issues:
            text = "📭 **История пуста**"
            await event.edit(text, buttons=back_button("nav:main"))
            return

        text = f"🕘 **История заявок** ({len(issues)} шт.)"
        await event.edit(text, buttons=admin_history_list(issues, page))

    @client.on(events.CallbackQuery(pattern=rb"^page:history:(\d+)$"))
    @admin_only
    async def cb_page_history(event):
        """Пагинация истории."""
        page = int(event.pattern_match.group(1).decode())
        await show_history(event, page)

    # ================================================================
    # РАЗДЕЛ МЕНЕДЖЕРЫ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^nav:managers$"))
    @admin_only
    async def cb_nav_managers(event):
        """Экран списка менеджеров с активными аккаунтами."""
        await show_managers_list(event, page=0)

    async def show_managers_list(event, page: int = 0):
        """Показать список менеджеров с аккаунтами."""
        async with get_session() as session:
            managers = await issues_service.get_managers_with_accounts(session)

        if not managers:
            text = "📭 **Нет менеджеров с активными аккаунтами**"
            await event.edit(text, buttons=back_button("nav:main"))
            return

        total_accounts = sum(m.get("accounts_count", 0) for m in managers)
        text = (
            f"👥 **Менеджеры** ({len(managers)} чел.)\n"
            f"📱 Всего выдано аккаунтов: {total_accounts}\n\n"
            f"Выберите менеджера для просмотра:"
        )
        await event.edit(text, buttons=admin_managers_list(managers, page))

    @client.on(events.CallbackQuery(pattern=rb"^mgr_admin:page:(\d+)$"))
    @admin_only
    async def cb_managers_page(event):
        """Пагинация списка менеджеров."""
        page = int(event.pattern_match.group(1).decode())
        await show_managers_list(event, page)

    @client.on(events.CallbackQuery(pattern=rb"^mgr_admin:detail:(\d+)$"))
    @admin_only
    async def cb_manager_detail(event):
        """Детали менеджера с его аккаунтами."""
        user_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            user = await issues_service.get_user_by_id(session, user_id)
            if not user:
                await event.answer("Менеджер не найден", alert=True)
                return

            issues = await issues_service.get_user_active_issues(session, user_id)

        username = f"@{user.username}" if user.username else f"ID:{user.tg_id}"
        full_name = user.full_name or ""

        text = (
            f"👤 **Менеджер: {username}**\n"
            f"{full_name}\n"
            f"🆔 TG ID: `{user.tg_id}`\n\n"
            f"📱 **Активных аккаунтов: {len(issues)}**\n"
        )

        if issues:
            text += "\nСписок аккаунтов:"
            for i, issue in enumerate(issues[:10], 1):
                acc = issue.account
                if acc:
                    phone = acc.phone or f"#{acc.id}"
                    premium = "⭐" if acc.is_premium else ""
                    issued = (
                        issue.approved_at.strftime("%d.%m %H:%M")
                        if issue.approved_at
                        else "?"
                    )
                    text += f"\n{i}. `{phone}` {premium} • {issued}"

        await event.edit(text, buttons=admin_manager_detail(user_id, issues))

    @client.on(events.CallbackQuery(pattern=rb"^mgr_admin:revoke_one:(\d+)$"))
    @admin_only
    async def cb_manager_revoke_one(event):
        """Отзыв одного аккаунта у менеджера (переадресация на стандартный отзыв)."""
        issue_id = int(event.pattern_match.group(1).decode())

        text = f"⚠️ **Отозвать аккаунт по заявке #{issue_id}?**"
        await event.edit(text, buttons=confirm_revoke(issue_id))

    @client.on(events.CallbackQuery(pattern=rb"^mgr_admin:revoke_all:(\d+)$"))
    @admin_only
    async def cb_manager_revoke_all_confirm(event):
        """Запрос подтверждения отзыва всех аккаунтов."""
        user_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            issues = await issues_service.get_user_active_issues(session, user_id)
            user = await issues_service.get_user_by_id(session, user_id)

        if not issues:
            await event.answer("У менеджера нет активных аккаунтов", alert=True)
            return

        username = f"@{user.username}" if user and user.username else f"ID:{user_id}"
        text = (
            f"⚠️ **Отозвать ВСЕ аккаунты у {username}?**\n\n"
            f"Будет отозвано: {len(issues)} шт."
        )
        await event.edit(text, buttons=confirm_revoke_all(user_id, len(issues)))

    @client.on(events.CallbackQuery(pattern=rb"^mgr_admin:confirm_revoke_all:(\d+)$"))
    @admin_only
    async def cb_manager_revoke_all(event):
        """Подтверждение отзыва всех аккаунтов у менеджера."""
        user_id = int(event.pattern_match.group(1).decode())

        revoked_count = 0
        manager_tg_id = None

        async with get_session() as session:
            user = await issues_service.get_user_by_id(session, user_id)
            if user:
                manager_tg_id = user.tg_id

            issues = await issues_service.get_user_active_issues(session, user_id)

            for issue in issues:
                if issue.account:
                    # Жёсткий отзыв: сбрасываем все другие Telegram-сессии аккаунта
                    # (менеджера выбросит из Telegram на устройстве)
                    try:
                        await reset_other_sessions(
                            account_id=issue.account.id,
                            session_path=issue.account.session_path,
                            account_phone=getattr(issue.account, "phone", None),
                        )
                    except Exception as e:
                        logger.warning(
                            f"Reset sessions failed for account_id={issue.account.id}: {e}"
                        )

                    await accounts_service.release_account(session, issue.account)
                    await stop_code_listener(issue.account.id)

                await issues_service.revoke_issue(session, issue)
                revoked_count += 1

        # Уведомляем менеджера
        if manager_tg_id:
            try:
                await client.send_message(
                    manager_tg_id,
                    f"🔴 **Все аккаунты отозваны**\n\n"
                    f"Администратор отозвал {revoked_count} аккаунтов.",
                )
            except Exception as e:
                logger.warning(f"Failed to notify manager {manager_tg_id}: {e}")

        text = f"✅ **Отозвано {revoked_count} аккаунтов**"
        await event.edit(text, buttons=back_button("nav:managers"))
        logger.info(
            f"Revoked {revoked_count} accounts from user {user_id} by admin {event.sender_id}"
        )

    # ================================================================
    # ДЕТАЛИ ЗАЯВКИ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^issue:detail:(\d+)$"))
    @admin_only
    async def cb_issue_detail(event):
        """Детали заявки."""
        issue_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

        if not issue:
            await event.edit("❌ Заявка не найдена", buttons=admin_issue_processed())
            return

        user = issue.user
        acc = issue.account

        status_val = (
            issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        )
        emoji = ISSUE_STATUS_EMOJI.get(status_val, "⚪")
        status_name = ISSUE_STATUS_NAMES.get(status_val, status_val)

        text = (
            f"📋 **Заявка #{issue.id}**\n\n"
            f"👤 Пользователь: @{user.username if user else 'нет'}\n"
            f"🆔 ID: `{user.tg_id if user else '?'}`\n"
            f"{emoji} Статус: {status_name}\n"
        )

        if acc:
            text += f"\n📱 Аккаунт: `{acc.phone}`"

        # Информация о коде подтверждения
        if issue.confirmation_code:
            text += f"\n🔑 Код: получен ✅"
        elif status_val == "approved":
            text += f"\n🔑 Код: ожидается..."

        if issue.requested_at:
            text += f"\n📅 Создана: {issue.requested_at.strftime('%d.%m.%Y %H:%M')}"

        if issue.approved_at:
            text += f"\n✅ Одобрена: {issue.approved_at.strftime('%d.%m.%Y %H:%M')}"

        has_account = acc is not None
        await event.edit(
            text, buttons=issue_detail_buttons(issue_id, status_val, has_account)
        )

    # ================================================================
    # ОДОБРЕНИЕ/ОТКЛОНЕНИЕ ЗАЯВОК
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^issue:approve:(\d+)$"))
    @admin_only
    async def cb_approve(event):
        """Одобрить заявку."""
        issue_id = int(event.pattern_match.group(1).decode())

        # Защита от двойных кликов
        try:
            await event.edit("⏳ Обрабатываю заявку...", buttons=None)
        except Exception:
            pass

        # Данные для отправки после закрытия сессии
        manager_tg_id = None
        account_phone = None
        account_id = None
        account_session_path = None
        account_is_premium = False
        can_request_more = False
        manager_username = None
        proxy_dict = None
        proxy_display = None
        account_api_id = None
        account_api_hash = None

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

            if not issue:
                await event.edit(
                    "❌ Заявка не найдена", buttons=admin_issue_processed()
                )
                return

            if issue.status != IssueStatus.PENDING:
                await event.edit(
                    f"ℹ️ Заявка уже обработана: {issue.status.value}",
                    buttons=admin_issue_processed(),
                )
                return

            # Атомарно получаем и блокируем аккаунт (защита от race condition)
            account = await accounts_service.get_free_account_with_lock(session)
            if not account:
                await event.edit(
                    "❌ Нет свободных аккаунтов!", buttons=admin_issue_processed()
                )
                return

            # Автоматически назначаем прокси если нет и есть доступные
            if not account.proxy_id:
                assigned_proxy = await proxy_service.assign_proxy_to_account(
                    session, account.id
                )
                if assigned_proxy:
                    logger.info(
                        f"Auto-assigned proxy {assigned_proxy.id} to account {account.id}"
                    )

            # Получаем прокси для передачи в воркер
            if account.proxy_id:
                proxy_obj = await proxy_service.get_proxy_by_id(
                    session, account.proxy_id
                )
                if proxy_obj and proxy_obj.is_active:
                    proxy_dict = proxy_obj.to_telethon_dict()
                    proxy_display = proxy_obj.display_string

            # Аккаунт уже помечен как ASSIGNED в get_free_account_with_lock
            await issues_service.approve_issue(session, issue, account)

            # Сохраняем данные до закрытия сессии
            manager_tg_id = issue.user.tg_id
            manager_username = issue.user.username
            account_phone = account.phone
            account_id = account.id
            account_session_path = account.session_path
            account_is_premium = account.is_premium
            account_api_id = account.api_id
            account_api_hash = account.api_hash
            # Device fingerprint
            account_device_model = account.device_model
            account_system_version = account.system_version
            account_app_version = account.app_version
            account_lang_code = account.lang_code
            account_system_lang_code = account.system_lang_code

            # Проверяем лимит менеджера
            active_count = await issues_service.count_active_by_user(
                session, issue.user.id
            )
            can_request_more = active_count < settings.max_accounts_per_manager

        # Обновляем сообщение админу (после коммита в БД)
        proxy_line_admin = f"🌐 Прокси: `{proxy_display}`\n" if proxy_display else ""
        await event.edit(
            f"✅ **Заявка #{issue_id} одобрена**\n\n"
            f"📞 Аккаунт: `{account_phone}`\n"
            f"{proxy_line_admin}"
            f"👤 Выдан: @{manager_username or manager_tg_id}",
            buttons=admin_issue_processed(),
        )

        # Уведомляем менеджера (без прокси - только для админов)
        try:
            premium_line = "⭐ Telegram Premium\n" if account_is_premium else ""
            phone_line = (
                f"📞 Номер: `{account_phone}`\n"
                if account_phone
                else "📞 Номер: определяется...\n"
            )
            await client.send_message(
                manager_tg_id,
                f"🎉 **Аккаунт выдан!**\n\n"
                f"{phone_line}"
                f"{premium_line}"
                f"🔐 Облачный пароль: `100300`\n\n"
                f"⏳ Ожидай код подтверждения...",
                buttons=manager_account_issued(can_request_more),
            )
            logger.info(f"Notification sent to manager {manager_tg_id}")
        except Exception as e:
            logger.error(f"Failed to notify manager {manager_tg_id}: {e}")

        # Запускаем слушатель кода
        try:
            callbacks = _create_code_callbacks(client, issue_id)

            await start_code_listener(
                account_id=account_id,
                session_path=account_session_path,
                manager_tg_id=manager_tg_id,
                on_code_received=callbacks["on_code"],
                on_timeout=callbacks["on_timeout"],
                on_error=callbacks["on_error"],
                bot_client=client,
                proxy=proxy_dict,
                api_id=account_api_id,
                api_hash=account_api_hash,
                account_phone=account_phone,
                # Device fingerprint
                device_model=account_device_model,
                system_version=account_system_version,
                app_version=account_app_version,
                lang_code=account_lang_code,
                system_lang_code=account_system_lang_code,
                # Callback для отправки номера телефона после подключения
                on_connected=callbacks["on_connected"],
            )
        except Exception as e:
            logger.error(f"Failed to start code listener: {e}")

        logger.info(f"Issue #{issue_id} approved by admin {event.sender_id}")

    @client.on(events.CallbackQuery(pattern=rb"^issue:reject:(\d+)$"))
    @admin_only
    async def cb_reject(event):
        """Отклонить заявку."""
        issue_id = int(event.pattern_match.group(1).decode())

        # Защита от двойных кликов
        await event.answer("⏳ Обрабатываю...")

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

            if not issue:
                await event.edit(
                    "❌ Заявка не найдена", buttons=admin_issue_processed()
                )
                return

            if issue.status != IssueStatus.PENDING:
                await event.answer("Заявка уже обработана", alert=True)
                return

            await issues_service.reject_issue(session, issue)

            await event.edit(
                f"❌ **Заявка #{issue_id} отклонена**", buttons=admin_issue_processed()
            )

            await client.send_message(
                issue.user.tg_id,
                f"❌ **Заявка #{issue_id} отклонена**\n\n"
                f"Обратитесь к администратору для уточнения причины.",
            )

    # @delete

    # ================================================================
    # ОТЗЫВ АККАУНТА
    # ================================================================

    # @client.on(events.CallbackQuery(pattern=rb"^issue:revoke:(\d+)$"))
    # @admin_only
    # async def cb_revoke_confirm(event):
    #     """Запрос подтверждения отзыва."""
    #     issue_id = int(event.pattern_match.group(1).decode())

    #     text = f"⚠️ **Отозвать аккаунт по заявке #{issue_id}?**"
    #     await event.edit(text, buttons=confirm_revoke(issue_id))

    # @client.on(events.CallbackQuery(pattern=rb"^issue:confirm_revoke:(\d+)$"))
    # @admin_only
    # async def cb_revoke(event):
    #     """Подтверждение отзыва."""
    #     issue_id = int(event.pattern_match.group(1).decode())

    #     async with get_session() as session:
    #         issue = await issues_service.get_issue_by_id(session, issue_id)

    #         if not issue:
    #             await event.edit(
    #                 "❌ Заявка не найдена", buttons=admin_issue_processed()
    #             )
    #             return

    #         if issue.status != IssueStatus.APPROVED:
    #             await event.answer(
    #                 f"Нельзя отозвать: статус {issue.status.value}", alert=True
    #             )
    #             return

    #         if issue.account:
    #             # Жёсткий отзыв: сбрасываем все другие Telegram-сессии аккаунта
    #             try:
    #                 await reset_other_sessions(
    #                     account_id=issue.account.id,
    #                     session_path=issue.account.session_path,
    #                     account_phone=getattr(issue.account, "phone", None),
    #                 )
    #             except Exception as e:
    #                 logger.warning(
    #                     f"Reset sessions failed for account_id={issue.account.id}: {e}"
    #                 )

    #             await accounts_service.release_account(session, issue.account)
    #             await stop_code_listener(issue.account.id)

    #         await issues_service.revoke_issue(session, issue)

    #         await event.edit(
    #             f"🔴 **Выдача #{issue_id} отозвана**", buttons=admin_issue_processed()
    #         )

    #         await client.send_message(
    #             issue.user.tg_id,
    #             f"🔴 **Аккаунт отозван**\n\n"
    #             f"Выдача #{issue_id} была отозвана администратором.",
    #         )

    #         logger.info(f"Issue #{issue_id} revoked by admin {event.sender_id}")
    # @delete

    @client.on(events.CallbackQuery(pattern=rb"^issue:confirm_revoke:(\d+)$"))
    @admin_only
    async def cb_revoke(event):
        """Подтверждение отзыва с транзакцией."""
        issue_id = int(event.pattern_match.group(1).decode())

        # Сохраняем ID менеджера для уведомления до закрытия транзакции
        manager_tg_id = None
        account_phone = None

        try:
            async with get_session() as session:
                # 1. НАЧИНАЕМ ЯВНУЮ ТРАНЗАКЦИЮ
                async with session.begin():
                    issue = await issues_service.get_issue_by_id(session, issue_id)

                    if not issue:
                        # Отменяем транзакцию (нечего делать)
                        raise ValueError(f"Заявка #{issue_id} не найдена")

                    if issue.status != IssueStatus.APPROVED:
                        raise ValueError(
                            f"Нельзя отозвать: статус {issue.status.value}"
                        )

                    # Сохраняем данные для уведомления
                    manager_tg_id = issue.user.tg_id if issue.user else None
                    account_phone = issue.account.phone if issue.account else None

                    if issue.account:
                        # 2. Жёсткий отзыв сессий (внешний вызов, делаем до основной логики)
                        # В идеале это тоже должно быть в транзакции, но это внешняя операция
                        try:
                            await reset_other_sessions(
                                account_id=issue.account.id,
                                session_path=issue.account.session_path,
                                account_phone=getattr(issue.account, "phone", None),
                            )
                        except Exception as e:
                            logger.warning(
                                f"Reset sessions failed for account_id={issue.account.id}: {e}"
                            )
                            # НЕ прерываем транзакцию - это не критично

                        # 3. КРИТИЧЕСКИ ВАЖНО: полный сброс аккаунта
                        # Убедитесь, что accounts_service.release_account делает:
                        # - status = AccountStatus.FREE
                        # - proxy_id = NULL
                        # - user_id = NULL
                        # - reserved_for_issue_id = NULL (если есть)
                        await accounts_service.release_account(session, issue.account)

                        # 4. Явно отвязываем аккаунт от заявки
                        issue.account = None

                    # 5. Меняем статус заявки
                    await issues_service.revoke_issue(session, issue)

                    # 6. Транзакция завершится автоматически (коммит) при выходе из контекста
                    logger.info(f"Transaction commit: issue #{issue_id} revoked")

            # 7. ДЕЙСТВИЯ ПОСЛЕ УСПЕШНОЙ ТРАНЗАКЦИИ (вне транзакции)

            # Останавливаем слушатель кода (если был запущен)
            if issue and issue.account:  # issue.account теперь None, но issue ещё есть
                await stop_code_listener(issue.account.id)

            # Уведомляем админа об успехе
            await event.edit(
                f"🔴 **Выдача #{issue_id} отозвана**", buttons=admin_issue_processed()
            )

            # Уведомляем менеджера (если есть контакт)
            if manager_tg_id:
                try:
                    await client.send_message(
                        manager_tg_id,
                        f"🔴 **Аккаунт отозван**\n\n"
                        f"Выдача #{issue_id} была отозвана администратором."
                        + (f"\n📱 Аккаунт: `{account_phone}`" if account_phone else ""),
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify manager {manager_tg_id}: {e}")

            logger.info(f"Issue #{issue_id} revoked by admin {event.sender_id}")

        except Exception as e:
            # 8. ОБРАБОТКА ОШИБОК (транзакция откатится автоматически)
            logger.error(f"Revoke transaction failed for issue #{issue_id}: {e}")

            error_msg = str(e)
            if "Нельзя отозвать" in error_msg or "не найдена" in error_msg:
                await event.answer(error_msg, alert=True)
            else:
                await event.edit(
                    f"❌ **Ошибка отзыва**\n\n"
                    f"Заявка #{issue_id}: {error_msg[:100]}",
                    buttons=admin_issue_processed(),
                )

            # Транзакция уже откатилась, никаких дополнительных действий не нужно

    # ================================================================
    # СКАЧИВАНИЕ АККАУНТА / ЗАПРОС КОДА
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^issue:download_session:(\d+)$"))
    @admin_only
    async def cb_download_session(event):
        """Скачать аккаунт как .session файл."""
        issue_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

            if not issue or not issue.account:
                await event.answer("Аккаунт не найден", alert=True)
                return

            acc = issue.account
            if not acc.session_path or not os.path.exists(acc.session_path):
                await event.answer("Session файл не найден", alert=True)
                return

            await event.answer("📤 Отправляю файл...")

            try:
                await client.send_file(
                    event.sender_id,
                    acc.session_path,
                    caption=f"📄 Session для аккаунта `{acc.phone}`",
                )
            except Exception as e:
                logger.error(f"Failed to send session file: {e}")
                await event.answer(f"Ошибка: {e}", alert=True)

    @client.on(events.CallbackQuery(pattern=rb"^issue:download_tdata:(\d+)$"))
    @admin_only
    async def cb_download_tdata(event):
        """Скачать аккаунт как tdata архив."""
        issue_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

            if not issue or not issue.account:
                await event.answer("Аккаунт не найден", alert=True)
                return

            acc = issue.account

            # Проверяем наличие tdata
            if acc.tdata_path and os.path.exists(acc.tdata_path):
                # Архивируем и отправляем
                await event.answer("📦 Архивирую tdata...")

                import tempfile
                import zipfile

                try:
                    with tempfile.NamedTemporaryFile(
                        suffix=".zip", delete=False
                    ) as tmp:
                        tmp_path = tmp.name

                    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        for root, dirs, files in os.walk(acc.tdata_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(
                                    file_path, os.path.dirname(acc.tdata_path)
                                )
                                zf.write(file_path, arcname)

                    await client.send_file(
                        event.sender_id,
                        tmp_path,
                        caption=f"📦 TData для аккаунта `{acc.phone}`",
                    )

                    os.remove(tmp_path)
                except Exception as e:
                    logger.error(f"Failed to send tdata: {e}")
                    await event.answer(f"Ошибка: {e}", alert=True)
            else:
                await event.answer("TData не найден для этого аккаунта", alert=True)

    @client.on(events.CallbackQuery(pattern=rb"^issue:request_code:(\d+)$"))
    @admin_only
    async def cb_request_code(event):
        """Запросить код подтверждения для админа."""
        issue_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            issue = await issues_service.get_issue_by_id(session, issue_id)

            if not issue or not issue.account:
                await event.answer("Аккаунт не найден", alert=True)
                return

            acc = issue.account

            if not acc.session_path:
                await event.answer("Session файл не найден", alert=True)
                return

            # Сохраняем данные до закрытия сессии
            account_id = acc.id
            account_phone = acc.phone
            account_session_path = acc.session_path
            account_api_id = acc.api_id
            account_api_hash = acc.api_hash
            # Device fingerprint
            account_device_model = acc.device_model
            account_system_version = acc.system_version
            account_app_version = acc.app_version
            account_lang_code = acc.lang_code
            account_system_lang_code = acc.system_lang_code

        await event.answer("⏳ Проверяю аккаунт...")

        # Проверяем валидность сессии перед запуском слушателя
        # Используем skip_connect=True чтобы не убить сессию лишним подключением
        validation = await session_import_service.validate_session(
            account_session_path,
            api_id=account_api_id,
            api_hash=account_api_hash,
            skip_connect=True,  # НЕ подключаемся - просто проверяем файлы
        )

        if not validation.success:
            await event.respond(
                f"❌ **Аккаунт невалиден**\n\n"
                f"📱 Телефон: `{account_phone}`\n\n"
                f"Сессия истекла или была отозвана."
            )
            return

        await event.respond("✅ Аккаунт валиден, запускаю слушатель кода...")

        # Создаём callbacks для админа
        admin_id = event.sender_id

        async def on_code_admin(acc_id: int, mgr_id: int, code: str):
            await client.send_message(
                admin_id,
                f"🔑 **Код получен!**\n\n"
                f"```\n{code}\n```\n\n"
                f"📱 Аккаунт: `{account_phone}`",
            )

        async def on_timeout_admin(acc_id: int, mgr_id: int):
            await client.send_message(
                admin_id,
                f"⏰ **Таймаут**\n\n" f"Код для аккаунта `{account_phone}` не получен.",
            )

        async def on_error_admin(acc_id: int, mgr_id: int, error: str):
            await client.send_message(admin_id, f"❌ **Ошибка:** {error}")

        try:
            await start_code_listener(
                account_id=account_id,
                session_path=account_session_path,
                manager_tg_id=admin_id,
                on_code_received=on_code_admin,
                on_timeout=on_timeout_admin,
                on_error=on_error_admin,
                bot_client=client,
                api_id=account_api_id,
                api_hash=account_api_hash,
                account_phone=account_phone,
                # Device fingerprint
                device_model=account_device_model,
                system_version=account_system_version,
                app_version=account_app_version,
                lang_code=account_lang_code,
                system_lang_code=account_system_lang_code,
            )

            await client.send_message(
                admin_id,
                f"⏳ **Ожидаю код...**\n\n"
                f"📱 Аккаунт: `{account_phone}`\n"
                f"⏱ Таймаут: {settings.code_wait_timeout} сек.\n\n"
                f"💡 Теперь попробуйте войти в этот аккаунт с другого устройства.",
            )
        except Exception as e:
            logger.error(f"Failed to start code listener for admin: {e}")
            await event.answer(f"Ошибка: {e}", alert=True)

    # ================================================================
    # LEGACY КОМАНДЫ (fallback)
    # ================================================================

    @client.on(events.NewMessage(pattern=r"^/accounts$"))
    @admin_only
    async def cmd_accounts(event):
        """Список аккаунтов (команда)."""
        async with get_session() as session:
            accounts = await accounts_service.get_all_accounts(session)

        if not accounts:
            await event.respond("📭 Аккаунтов нет", buttons=main_menu_admin())
            return

        text = f"🗂 **Аккаунты** ({len(accounts)} шт.)\n\nВыберите фильтр:"
        await event.respond(text, buttons=admin_accounts_filter())

    @client.on(events.NewMessage(pattern=r"^/active$"))
    @admin_only
    async def cmd_active(event):
        """Активные выдачи (команда)."""
        async with get_session() as session:
            issues = await issues_service.get_active_issues(session)

        if not issues:
            await event.respond("📭 Нет активных выдач", buttons=main_menu_admin())
            return

        text = f"✅ **Активные выдачи** ({len(issues)} шт.)"
        await event.respond(text, buttons=admin_active_issues_list(issues))

    @client.on(events.NewMessage(pattern=r"^/issues$"))
    @admin_only
    async def cmd_issues(event):
        """История заявок (команда)."""
        async with get_session() as session:
            issues = await issues_service.get_all_issues(session, limit=100)

        if not issues:
            await event.respond("📭 История пуста", buttons=main_menu_admin())
            return

        text = f"🕘 **История заявок** ({len(issues)} шт.)"
        await event.respond(text, buttons=admin_history_list(issues))

    @client.on(events.NewMessage(pattern=r"^/stats$"))
    @admin_only
    async def cmd_stats(event):
        """Статистика (команда)."""
        async with get_session() as session:
            stats = await get_system_stats(session)

        text = format_stats_message(stats)
        await event.respond(text, buttons=main_menu_admin())

    @client.on(events.NewMessage(pattern=r"^/health$"))
    @admin_only
    async def cmd_health(event):
        """Health check (команда)."""
        await event.respond("⏳ Проверяю систему...")
        health = await run_health_check()
        report = format_health_report(health)
        await event.respond(report, buttons=main_menu_admin())

    @client.on(events.NewMessage(pattern=r"^/add_session$"))
    @admin_only
    async def cmd_add_session(event):
        """Справка по импорту session."""
        _user_states[event.sender_id] = {"mode": "import_session"}
        await event.respond(
            "📄 **Импорт Session**\n\n" "Отправьте файл `.session` документом.",
            buttons=back_button("nav:main"),
        )

    @client.on(events.NewMessage(pattern=r"^/add_tdata$"))
    @admin_only
    async def cmd_add_tdata(event):
        """Справка по импорту tdata."""
        _user_states[event.sender_id] = {"mode": "import_tdata"}
        await event.respond(
            "📦 **Импорт TData**\n\n" "Отправьте ZIP-архив с tdata.",
            buttons=back_button("nav:main"),
        )

    # ================================================================
    # ПРОКСИ
    # ================================================================

    @client.on(events.CallbackQuery(pattern=rb"^nav:proxies$"))
    @admin_only
    async def cb_nav_proxies(event):
        """Главное меню прокси."""
        async with get_session() as session:
            stats = await proxy_service.get_proxy_stats(session)

        text = (
            f"🌐 **Прокси-серверы**\n\n"
            f"📊 Всего: {stats['total']}\n"
            f"🟢 Активных: {stats['active']}\n"
            f"🔴 Неактивных: {stats['inactive']}\n"
            f"🔗 Аккаунтов с прокси: {stats['accounts_with_proxy']}"
        )
        await event.edit(text, buttons=admin_proxies_menu(stats))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:list$"))
    @admin_only
    async def cb_proxy_list(event):
        """Список всех прокси."""
        async with get_session() as session:
            proxies = await proxy_service.get_all_proxies(session)

        if not proxies:
            text = "📋 **Список прокси**\n\n_Прокси не добавлены._"
            await event.edit(
                text,
                buttons=[
                    [Button.inline("➕ Добавить", data=CB.PROXY_ADD)],
                    [Button.inline("⬅️ Назад", data="nav:proxies")],
                ],
            )
            return

        text = f"📋 **Список прокси** ({len(proxies)})"
        await event.edit(text, buttons=admin_proxies_list(proxies, page=0))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:page:(\d+)$"))
    @admin_only
    async def cb_proxy_page(event):
        """Пагинация списка прокси."""
        page = int(event.pattern_match.group(1).decode())
        async with get_session() as session:
            proxies = await proxy_service.get_all_proxies(session)

        text = f"📋 **Список прокси** ({len(proxies)})"
        await event.edit(text, buttons=admin_proxies_list(proxies, page=page))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:add$"))
    @admin_only
    async def cb_proxy_add(event):
        """Выбор типа прокси перед добавлением."""
        text = "➕ **Добавление прокси**\n\n" "Выберите тип прокси:"
        buttons = [
            [Button.inline("🔷 SOCKS5", data=b"proxy:add_type:socks5")],
            [Button.inline("� HTTP", data=b"proxy:add_type:http")],
            [Button.inline("🟣 HTTPS", data=b"proxy:add_type:https")],
            [Button.inline("⬅️ Назад", data=b"nav:proxies")],
        ]
        await event.edit(text, buttons=buttons)

    @client.on(events.CallbackQuery(pattern=rb"^proxy:add_type:(socks5|http|https)$"))
    @admin_only
    async def cb_proxy_add_type(event):
        """Выбран тип прокси, ожидаем список."""
        proxy_type = event.pattern_match.group(1).decode()
        _user_states[event.sender_id] = {
            "mode": "import_proxy",
            "proxy_type": proxy_type,
        }

        type_names = {
            "socks5": "🔷 SOCKS5",
            "http": "🟢 HTTP",
            "https": "🟣 HTTPS",
        }

        text = (
            f"➕ **Добавление прокси** ({type_names[proxy_type]})\n\n"
            "Отправьте список прокси (каждый на новой строке).\n\n"
            "**Поддерживаемые форматы:**\n"
            "• `host:port`\n"
            "• `user:pass@host:port`\n"
            "• `login:password@ip:port`\n\n"
            f"_Все прокси будут добавлены как {proxy_type.upper()}._"
        )
        await event.edit(text, buttons=back_button("proxy:add"))

    @client.on(
        events.NewMessage(
            func=lambda e: (
                e.is_private
                and e.text
                and not e.text.startswith("/")
                and _user_states.get(e.sender_id, {}).get("mode") == "import_proxy"
            )
        )
    )
    @admin_only
    async def handle_proxy_text(event):
        """Обработка текста с прокси."""
        # Получаем и очищаем состояние
        state = _user_states.pop(event.sender_id, {})
        proxy_type_str = state.get("proxy_type", "socks5")

        # Конвертируем строку в ProxyType
        from db.models import ProxyType

        type_map = {
            "socks5": ProxyType.SOCKS5,
            "http": ProxyType.HTTP,
            "https": ProxyType.HTTPS,
        }
        default_type = type_map.get(proxy_type_str, ProxyType.SOCKS5)

        text = event.text.strip()
        if not text:
            await event.respond("❌ Пустой текст", buttons=back_button("nav:proxies"))
            return

        # Импортируем прокси
        async with get_session() as session:
            new_count, updated_count, errors = await proxy_service.import_proxies(
                session, text, default_type=default_type
            )

        total_imported = new_count + updated_count

        if total_imported > 0:
            # Автоматически проверяем добавленные прокси
            await event.respond(
                f"⏳ **Импортировано {total_imported} прокси**\n\n"
                f"🔍 Проверяю работоспособность..."
            )

            working = 0
            failed = 0

            async with get_session() as session:
                proxies = await proxy_service.get_all_proxies(session)
                # Берём только что добавленные (последние по дате)
                proxies_to_check = proxies[:total_imported]

                for proxy in proxies_to_check:
                    is_ok, ip, latency = await proxy_service.check_proxy(proxy)

                    # Определяем страну если прокси рабочий
                    country = None
                    if is_ok and ip:
                        country = await proxy_service.get_country_by_ip(ip)

                    await proxy_service.update_proxy_check_result(
                        session,
                        proxy.id,
                        is_ok,
                        ip,
                        latency,
                        country=country,
                        auto_commit=False,
                    )

                    if is_ok:
                        working += 1
                    else:
                        failed += 1

                await session.commit()

            result_text = f"✅ **Прокси импортированы** ({proxy_type_str.upper()})\n\n"
            result_text += f"➕ Добавлено: {new_count}\n"
            result_text += f"🔄 Обновлено: {updated_count}\n\n"
            result_text += f"📊 **Проверка:**\n"
            result_text += f"• 🟢 Рабочих: {working}\n"
            result_text += f"• 🔴 Нерабочих: {failed}\n"
        else:
            result_text = f"⚠️ **Прокси не импортированы**\n\n"

        if errors:
            result_text += f"\n⚠️ **Ошибки парсинга ({len(errors)}):**\n"
            for err in errors[:5]:
                result_text += f"• {err}\n"
            if len(errors) > 5:
                result_text += f"_...и ещё {len(errors) - 5} ошибок_"

        await event.respond(
            result_text,
            buttons=admin_add_proxy_result(new_count > 0 or updated_count > 0),
        )

    @client.on(events.CallbackQuery(pattern=rb"^proxy:detail:(\d+)$"))
    @admin_only
    async def cb_proxy_detail(event):
        """Детали прокси."""
        proxy_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            proxy = await proxy_service.get_proxy_by_id(session, proxy_id)
            if not proxy:
                await event.answer("Прокси не найден", alert=True)
                return

            accounts_count = await proxy_service.get_accounts_on_proxy(
                session, proxy_id
            )

        status = "🟢 Активен" if proxy.is_active else "🔴 Неактивен"
        latency = f"{proxy.latency_ms} ms" if proxy.latency_ms else "—"
        last_check = (
            proxy.last_checked_at.strftime("%d.%m %H:%M")
            if proxy.last_checked_at
            else "—"
        )
        last_ip = proxy.last_check_ip or "—"
        country_flag = proxy_service.get_country_flag(proxy.country)

        text = (
            f"🌐 **Прокси #{proxy.id}** {country_flag}\n\n"
            f"**Адрес:** `{proxy.display_string}`\n"
            f"**Тип:** {proxy.proxy_type.value.upper()}\n"
            f"**Статус:** {status}\n\n"
            f"📊 **Метрики:**\n"
            f"• Латентность: {latency}\n"
            f"• Последняя проверка: {last_check}\n"
            f"• IP при проверке: {last_ip}\n"
            f"• Успешных проверок: {proxy.success_count}\n"
            f"• Неудач подряд: {proxy.fail_count}\n\n"
            f"🔗 **Аккаунтов:** {accounts_count} / {proxy.max_accounts if proxy.max_accounts > 0 else '∞'}"
        )
        await event.edit(text, buttons=admin_proxy_detail(proxy, accounts_count))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:check_one:(\d+)$"))
    @admin_only
    async def cb_proxy_check_one(event):
        """Проверить один прокси."""
        proxy_id = int(event.pattern_match.group(1).decode())
        await event.answer("🔍 Проверяю прокси...")

        async with get_session() as session:
            proxy = await proxy_service.get_proxy_by_id(session, proxy_id)
            if not proxy:
                await event.answer("Прокси не найден", alert=True)
                return

            is_ok, ip, latency = await proxy_service.check_proxy(proxy)

            # Определяем страну по IP
            country = None
            if is_ok and ip:
                country = await proxy_service.get_country_by_ip(ip)

            await proxy_service.update_proxy_check_result(
                session, proxy_id, is_ok, ip, latency, country=country
            )

        if is_ok:
            flag = proxy_service.get_country_flag(country)
            await event.answer(f"✅ Работает! {flag} IP: {ip}, {latency}ms", alert=True)
        else:
            await event.answer("❌ Прокси не отвечает", alert=True)

        # Обновляем карточку
        async with get_session() as session:
            proxy = await proxy_service.get_proxy_by_id(session, proxy_id)
            accounts_count = await proxy_service.get_accounts_on_proxy(
                session, proxy_id
            )

        status = "🟢 Активен" if proxy.is_active else "🔴 Неактивен"
        latency_str = f"{proxy.latency_ms} ms" if proxy.latency_ms else "—"
        last_check = (
            proxy.last_checked_at.strftime("%d.%m %H:%M")
            if proxy.last_checked_at
            else "—"
        )
        last_ip = proxy.last_check_ip or "—"
        country_flag = proxy_service.get_country_flag(proxy.country)

        text = (
            f"🌐 **Прокси #{proxy.id}** {country_flag}\n\n"
            f"**Адрес:** `{proxy.display_string}`\n"
            f"**Тип:** {proxy.proxy_type.value.upper()}\n"
            f"**Статус:** {status}\n\n"
            f"📊 **Метрики:**\n"
            f"• Латентность: {latency_str}\n"
            f"• Последняя проверка: {last_check}\n"
            f"• IP при проверке: {last_ip}\n"
            f"• Успешных проверок: {proxy.success_count}\n"
            f"• Неудач подряд: {proxy.fail_count}\n\n"
            f"🔗 **Аккаунтов:** {accounts_count} / {proxy.max_accounts if proxy.max_accounts > 0 else '∞'}"
        )
        await event.edit(text, buttons=admin_proxy_detail(proxy, accounts_count))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:toggle:(\d+)$"))
    @admin_only
    async def cb_proxy_toggle(event):
        """Переключить активность прокси."""
        proxy_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            new_state = await proxy_service.toggle_proxy(session, proxy_id)
            if new_state is None:
                await event.answer("Прокси не найден", alert=True)
                return

            proxy = await proxy_service.get_proxy_by_id(session, proxy_id)
            accounts_count = await proxy_service.get_accounts_on_proxy(
                session, proxy_id
            )

        status_text = "включен" if new_state else "отключен"
        await event.answer(f"Прокси {status_text}", alert=False)

        status = "🟢 Активен" if proxy.is_active else "🔴 Неактивен"
        latency_str = f"{proxy.latency_ms} ms" if proxy.latency_ms else "—"

        text = (
            f"🌐 **Прокси #{proxy.id}**\n\n"
            f"**Адрес:** `{proxy.display_string}`\n"
            f"**Тип:** {proxy.proxy_type.value.upper()}\n"
            f"**Статус:** {status}\n\n"
            f"🔗 **Аккаунтов:** {accounts_count} / {proxy.max_accounts if proxy.max_accounts > 0 else '∞'}"
        )
        await event.edit(text, buttons=admin_proxy_detail(proxy, accounts_count))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:delete:(\d+)$"))
    @admin_only
    async def cb_proxy_delete(event):
        """Запрос удаления прокси."""
        proxy_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            proxy = await proxy_service.get_proxy_by_id(session, proxy_id)
            if not proxy:
                await event.answer("Прокси не найден", alert=True)
                return
            accounts_count = await proxy_service.get_accounts_on_proxy(
                session, proxy_id
            )

        text = f"🗑 **Удалить прокси?**\n\n" f"`{proxy.display_string}`\n\n"
        if accounts_count > 0:
            text += f"⚠️ К нему привязано {accounts_count} аккаунтов!\n"
            text += "Они будут отвязаны от прокси."

        await event.edit(text, buttons=confirm_delete_proxy(proxy_id))

    @client.on(events.CallbackQuery(pattern=rb"^proxy:confirm_delete:(\d+)$"))
    @admin_only
    async def cb_proxy_confirm_delete(event):
        """Подтверждение удаления прокси."""
        proxy_id = int(event.pattern_match.group(1).decode())

        async with get_session() as session:
            deleted = await proxy_service.delete_proxy(session, proxy_id)

        if deleted:
            await event.answer("Прокси удалён", alert=False)
            # Возвращаем к списку
            async with get_session() as session:
                proxies = await proxy_service.get_all_proxies(session)

            if proxies:
                text = f"📋 **Список прокси** ({len(proxies)})"
                await event.edit(text, buttons=admin_proxies_list(proxies, page=0))
            else:
                text = "📋 **Список прокси**\n\n_Прокси не добавлены._"
                await event.edit(
                    text,
                    buttons=[
                        [Button.inline("➕ Добавить", data=CB.PROXY_ADD)],
                        [Button.inline("⬅️ Назад", data="nav:proxies")],
                    ],
                )
        else:
            await event.answer("Не удалось удалить", alert=True)

    @client.on(events.CallbackQuery(pattern=rb"^proxy:check_all$"))
    @admin_only
    async def cb_proxy_check_all(event):
        """Проверить все прокси."""
        await event.answer("🔍 Проверяю все прокси... Это может занять время.")

        async with get_session() as session:
            working, failed = await proxy_service.check_all_proxies(
                session, only_active=False
            )
            stats = await proxy_service.get_proxy_stats(session)

        text = (
            f"🔍 **Проверка завершена**\n\n"
            f"✅ Работают: {working}\n"
            f"❌ Не работают: {failed}\n\n"
            f"📊 **Статистика:**\n"
            f"🟢 Активных: {stats['active']}\n"
            f"🔴 Неактивных: {stats['inactive']}"
        )
        await event.edit(text, buttons=admin_proxies_menu(stats))

    @client.on(events.NewMessage(pattern=r"^/proxies$"))
    @admin_only
    async def cmd_proxies(event):
        """Команда /proxies."""
        async with get_session() as session:
            stats = await proxy_service.get_proxy_stats(session)

        text = (
            f"🌐 **Прокси-серверы**\n\n"
            f"📊 Всего: {stats['total']}\n"
            f"🟢 Активных: {stats['active']}\n"
            f"🔴 Неактивных: {stats['inactive']}\n"
            f"🔗 Аккаунтов с прокси: {stats['accounts_with_proxy']}"
        )
        await event.respond(text, buttons=admin_proxies_menu(stats))


# ================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ================================================================


def _get_document_filename(doc) -> Optional[str]:
    """Извлечь имя файла из документа."""
    for attr in doc.attributes:
        if hasattr(attr, "file_name"):
            return attr.file_name
    return None


async def _cleanup_account_files(account) -> None:
    """Удалить файлы аккаунта."""
    sessions_root = os.path.abspath(settings.sessions_dir)

    if account.session_path and os.path.exists(account.session_path):
        os.remove(account.session_path)
        folder = os.path.abspath(os.path.dirname(account.session_path))
        # Не удалять корневую папку сессий
        if folder != sessions_root and os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)

    if account.tdata_path and os.path.exists(account.tdata_path):
        shutil.rmtree(account.tdata_path, ignore_errors=True)


async def _handle_session_file(event, client, filename: str) -> None:
    """Обработка .session файла."""
    await event.respond("⏳ Загружаю и проверяю сессию...")

    try:
        file_data = await client.download_media(event.document, bytes)

        async with get_session() as session:
            success, message, account = (
                await session_import_service.import_session_file(
                    session, file_data, filename
                )
            )
            await event.respond(message, buttons=admin_import_result(success))

    except Exception as e:
        logger.exception(f"Session import error: {e}")
        await event.respond(f"❌ Ошибка: {e}", buttons=admin_import_result(False))


async def _handle_tdata_archive(event, client, filename: str) -> None:
    """Обработка tdata архива."""
    await event.respond("⏳ Загружаю и распаковываю tdata...")

    try:
        file_data = await client.download_media(event.document, bytes)

        async with get_session() as session:
            success, message, account = await tdata_converter.import_tdata_archive(
                session, file_data, filename
            )
            await event.respond(message, buttons=admin_import_result(success))

    except Exception as e:
        logger.exception(f"TData import error: {e}")
        await event.respond(f"❌ Ошибка: {e}", buttons=admin_import_result(False))


async def _handle_batch_sessions_zip(event, client, filename: str) -> None:
    """Обработка ZIP-архива с пакетом сессий."""
    await event.respond("⏳ Загружаю архив и начинаю пакетный импорт...")

    try:
        file_data = await client.download_media(event.document, bytes)

        async with get_session() as session:
            report = await batch_import_service.import_zip(session, file_data, filename)

            message = report.format_message()
            success = report.successfully_imported > 0
            await event.respond(message, buttons=admin_import_result(success))

    except Exception as e:
        logger.exception(f"Batch import error: {e}")
        await event.respond(f"❌ Ошибка: {e}", buttons=admin_import_result(False))


async def _handle_tdata_import(event, filename: str) -> None:
    """Обработка ZIP-архива с tdata."""
    await event.respond("⏳ Загружаю и конвертирую tdata...")

    try:
        file_data = await event.client.download_media(event.document, bytes)

        async with get_session() as session:
            success, message, account = await tdata_converter.import_tdata_archive(
                session, file_data, filename
            )

            if success and account:
                text = (
                    f"✅ **Аккаунт импортирован**\n\n"
                    f"📱 Телефон: `{account.phone}`\n"
                    f"👤 Username: @{account.username or '—'}\n"
                    f"🆔 TG ID: `{account.tg_user_id}`\n"
                    f"💎 Premium: {'Да' if account.is_premium else 'Нет'}\n\n"
                    f"Статус: 🟢 Свободен"
                )
            else:
                text = f"❌ {message}"

            await event.respond(text, buttons=admin_import_result(success))

    except Exception as e:
        logger.exception(f"TData import error: {e}")
        await event.respond(f"❌ Ошибка: {e}", buttons=admin_import_result(False))


def _create_code_callbacks(client: TelegramClient, issue_id: int) -> dict:
    """Создать callbacks для слушателя кодов."""

    async def on_code_received(acc_id: int, mgr_id: int, code: str):
        async with get_session() as s:
            iss = await issues_service.get_issue_by_id(s, issue_id)
            if iss:
                await issues_service.set_confirmation_code(s, iss, code)

        await client.send_message(
            mgr_id,
            f"🔑 **Код подтверждения**\n\n"
            f"```\n{code}\n```\n\n"
            f"🔐 **Облачный пароль:** `100300`\n\n"
            f"Код действует ~5 минут.",
            buttons=manager_code_received(),
        )

        for admin_id in settings.admin_ids_list:
            try:
                await client.send_message(
                    admin_id, f"✅ Код для заявки #{issue_id} отправлен"
                )
            except Exception:
                pass

    async def on_timeout(acc_id: int, mgr_id: int):
        await client.send_message(
            mgr_id,
            f"⏰ **Код не получен**\n\n"
            f"Прошло {settings.code_wait_timeout // 60} минуты, код не пришёл в Telegram.\n\n"
            f"Возможные причины:\n"
            f"• Код пришёл по SMS\n"
            f"• Аккаунт требует пароль 2FA\n"
            f"• Слишком много попыток входа",
            buttons=manager_code_timeout(),
        )

        for admin_id in settings.admin_ids_list:
            try:
                await client.send_message(
                    admin_id,
                    f"⚠️ Таймаут кода для заявки #{issue_id}",
                )
            except Exception:
                pass

    async def on_error(acc_id: int, mgr_id: int, error_msg: str):
        await client.send_message(
            mgr_id,
            f"❌ **Ошибка:** {error_msg}\n\n" f"Обратись к администратору.",
            buttons=[[Button.inline("⬅️ В меню", data=CB.MGR_MENU)]],
        )

    async def on_connected(
        acc_id: int,
        mgr_id: int,
        phone: str | None,
        username: str | None,
        is_premium: bool,
    ):
        """Callback при успешном подключении к аккаунту - отправляем номер телефона."""
        if phone:
            premium_line = "⭐ Telegram Premium\n" if is_premium else ""
            username_line = f"👤 Username: @{username}\n" if username else ""
            try:
                await client.send_message(
                    mgr_id,
                    f"📱 **Данные аккаунта подтверждены**\n\n"
                    f"📞 Номер: `+{phone}`\n"
                    f"{username_line}"
                    f"{premium_line}"
                    f"🔐 Облачный пароль: `100300`",
                )
                logger.info(f"Sent phone update to manager {mgr_id}: +{phone}")
            except Exception as e:
                logger.warning(f"Failed to send phone update to manager {mgr_id}: {e}")

    return {
        "on_code": on_code_received,
        "on_timeout": on_timeout,
        "on_error": on_error,
        "on_connected": on_connected,
    }
