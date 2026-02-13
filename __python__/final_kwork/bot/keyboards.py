"""
Современные Inline-клавиатуры и меню бота.

Архитектура callback data:
- nav:<screen>             - навигация по экранам
- import:<type>            - импорт аккаунтов
- issue:<action>:<id>      - действия с заявками
- acc:<action>:<id>        - действия с аккаунтами
- filter:<type>:<page>     - фильтры с пагинацией
- page:<prefix>:<num>      - пагинация
- mgr:<action>             - действия менеджера
"""
from services.telethon_adapter import Button
from typing import List


# ============================================================
# CALLBACK DATA PREFIXES
# ============================================================

class CB:
    """Callback data константы."""
    # Навигация
    NAV = "nav"
    BACK = "back"
    NOOP = "noop"
    CLOSE = "close"
    
    # Импорт
    IMPORT_SESSION = "import:session"
    IMPORT_TDATA = "import:tdata"
    
    # Заявки
    ISSUE_APPROVE = "issue:approve"
    ISSUE_REJECT = "issue:reject"
    ISSUE_REVOKE = "issue:revoke"
    ISSUE_DETAIL = "issue:detail"
    ISSUE_CONFIRM_REVOKE = "issue:confirm_revoke"
    ISSUE_DOWNLOAD_SESSION = "issue:download_session"  # issue:download_session:{issue_id}
    ISSUE_DOWNLOAD_TDATA = "issue:download_tdata"      # issue:download_tdata:{issue_id}
    ISSUE_REQUEST_CODE = "issue:request_code"          # issue:request_code:{issue_id}
    
    # Аккаунты
    ACC_DETAIL = "acc:detail"
    ACC_DELETE = "acc:delete"
    ACC_CHECK = "acc:check"
    ACC_CONVERT = "acc:convert"
    ACC_CONFIRM_DELETE = "acc:confirm_delete"
    
    # Менеджер (новый стиль)
    MGR_MENU = "mgr:menu"
    MGR_GET = "mgr:get"
    MGR_STATUS = "mgr:status"
    MGR_MY = "mgr:my"
    MGR_HISTORY = "mgr:history"  # mgr:history:{page}
    MGR_HELP = "mgr:help"
    MGR_WAIT_CODE_AGAIN = "mgr:wait_code_again"
    MGR_CONTACT_ADMIN = "mgr:contact_admin"
    
    # Прокси
    PROXY_LIST = "proxy:list"
    PROXY_ADD = "proxy:add"
    PROXY_ADD_TYPE = "proxy:add_type"    # proxy:add_type:{type} - выбор типа
    PROXY_CHECK_ALL = "proxy:check_all"
    PROXY_DETAIL = "proxy:detail"        # proxy:detail:{id}
    PROXY_DELETE = "proxy:delete"        # proxy:delete:{id}
    PROXY_CONFIRM_DELETE = "proxy:confirm_delete"  # proxy:confirm_delete:{id}
    PROXY_TOGGLE = "proxy:toggle"        # proxy:toggle:{id}
    PROXY_CHECK_ONE = "proxy:check_one"  # proxy:check_one:{id}
    PROXY_ASSIGN = "proxy:assign"        # proxy:assign:{proxy_id}:{account_id}
    PROXY_UNASSIGN = "proxy:unassign"    # proxy:unassign:{account_id}
    
    # Менеджеры (для админа)
    MGR_LIST = "mgr_admin:list"          # Список менеджеров
    MGR_DETAIL = "mgr_admin:detail"      # mgr_admin:detail:{user_id}
    MGR_REVOKE_ALL = "mgr_admin:revoke_all"  # mgr_admin:revoke_all:{user_id}
    MGR_REVOKE_ONE = "mgr_admin:revoke_one"  # mgr_admin:revoke_one:{issue_id}
    MGR_CONFIRM_REVOKE_ALL = "mgr_admin:confirm_revoke_all"  # Подтверждение


# ============================================================
# ГЛАВНЫЕ МЕНЮ
# ============================================================

def main_menu_admin() -> List[List[Button]]:
    """
    Главное меню администратора (минималистичное).
    """
    return [
        [Button.inline("➕ Импорт", data="nav:import")],
        [Button.inline("🗂 Аккаунты", data="nav:accounts")],
        [Button.inline("👥 Менеджеры", data="nav:managers")],
        [Button.inline("🌐 Прокси", data="nav:proxies")],
        [Button.inline("⚙️ Настройки", data="nav:settings")],
    ]


def main_menu_manager() -> List[List[Button]]:
    """
    Главное меню менеджера (минималистичное).
    """
    return [
        [Button.inline("🧾 Получить аккаунт", data=CB.MGR_GET)],
        [Button.inline("📱 Мои аккаунты", data=CB.MGR_MY)],
    ]


# ============================================================
# ЭКРАНЫ АДМИНА
# ============================================================

def admin_import_menu() -> List[List[Button]]:
    """Меню импорта аккаунтов."""
    return [
        [Button.inline("📄 Импорт Session", data=CB.IMPORT_SESSION)],
        [Button.inline("📦 Импорт TData", data=CB.IMPORT_TDATA)],
        [Button.inline("⬅️ Назад", data="nav:main")],
    ]


def admin_import_result(success: bool = True) -> List[List[Button]]:
    """Кнопки после импорта."""
    return [
        [
            Button.inline("📥 Ещё", data="nav:import"),
            Button.inline("⬅️ Меню", data="nav:main"),
        ],
    ]


def admin_accounts_filter() -> List[List[Button]]:
    """Фильтры для списка аккаунтов."""
    return [
        [
            Button.inline("🟢 Свободные", data="filter:free:0"),
            Button.inline("🔵 Выданные", data="filter:assigned:0"),
        ],
        [
            Button.inline("🔴 Невалид", data="filter:disabled:0"),
            Button.inline("📋 Все", data="filter:all:0"),
        ],
        [Button.inline("⬅️ Назад", data="nav:main")],
    ]


def admin_accounts_list(
    accounts: list,
    filter_type: str,
    page: int = 0,
    per_page: int = 5
) -> List[List[Button]]:
    """Список аккаунтов с пагинацией."""
    buttons = []
    
    start = page * per_page
    end = start + per_page
    page_accounts = accounts[start:end]
    total_pages = max(1, (len(accounts) + per_page - 1) // per_page)
    
    status_emoji = {
        "free": "🟢", "assigned": "🔵", 
        "disabled": "🔴", "needs_conversion": "🟡",
    }
    
    for acc in page_accounts:
        status_val = acc.status.value if hasattr(acc.status, 'value') else str(acc.status)
        emoji = status_emoji.get(status_val, "⚪")
        premium = "⭐" if acc.is_premium else ""
        identifier = acc.phone or (f"@{acc.username}" if acc.username else None) or f"#{acc.id}"
        label = f"{emoji} {identifier} {premium}".strip()
        buttons.append([Button.inline(label, data=f"acc:detail:{acc.id}")])
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"filter:{filter_type}:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"filter:{filter_type}:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ К фильтрам", data="nav:accounts")])
    return buttons


def admin_account_detail(account, can_convert: bool = False) -> List[List[Button]]:
    """Детали аккаунта с действиями."""
    row1 = [Button.inline("🔍 Проверить", data=f"acc:check:{account.id}")]
    if can_convert:
        row1.append(Button.inline("🔄 Конверт.", data=f"acc:convert:{account.id}"))
    
    buttons = [
        row1,
        [
            Button.inline("🗑 Удалить", data=f"acc:delete:{account.id}"),
            Button.inline("⬅️ Назад", data="nav:accounts"),
        ],
    ]
    return buttons


def admin_active_issues_list(
    issues: list,
    page: int = 0,
    per_page: int = 5
) -> List[List[Button]]:
    """Список активных выдач."""
    buttons = []
    
    start = page * per_page
    end = start + per_page
    page_issues = issues[start:end]
    total_pages = max(1, (len(issues) + per_page - 1) // per_page)
    
    for issue in page_issues:
        user = issue.user
        acc = issue.account
        username = f"@{user.username}" if user and user.username else f"ID:{user.tg_id if user else '?'}"
        phone = acc.phone if acc else "?"
        
        buttons.append([
            Button.inline(f"#{issue.id} {username} {phone}", data=f"issue:detail:{issue.id}"),
            Button.inline("🔒", data=f"issue:revoke:{issue.id}"),
        ])
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"page:active:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"page:active:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ Назад", data="nav:main")])
    return buttons


def admin_history_list(
    issues: list,
    page: int = 0,
    per_page: int = 8
) -> List[List[Button]]:
    """История заявок."""
    buttons = []
    
    start = page * per_page
    end = start + per_page
    page_issues = issues[start:end]
    total_pages = max(1, (len(issues) + per_page - 1) // per_page)
    
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌", "revoked": "🔴"}
    
    for issue in page_issues:
        status_val = issue.status.value if hasattr(issue.status, 'value') else str(issue.status)
        emoji = status_emoji.get(status_val, "⚪")
        user = issue.user
        username = f"@{user.username}" if user and user.username else f"ID:{user.tg_id if user else '?'}"
        label = f"{emoji} #{issue.id} • {username}"
        buttons.append([Button.inline(label, data=f"issue:detail:{issue.id}")])
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"page:history:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"page:history:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ Назад", data="nav:main")])
    return buttons


# ============================================================
# КАРТОЧКИ ЗАЯВОК
# ============================================================

def admin_issue_card(issue_id: int) -> List[List[Button]]:
    """Кнопки одобрения/отклонения заявки для админа."""
    return [[
        Button.inline("✅ Подтвердить", data=f"issue:approve:{issue_id}"),
        Button.inline("❌ Отклонить", data=f"issue:reject:{issue_id}"),
    ]]


def admin_issue_processed() -> List[List[Button]]:
    """Кнопки после обработки заявки."""
    return [
        [Button.inline("⬅️ В меню", data="nav:main")],
    ]


def confirm_revoke(issue_id: int) -> List[List[Button]]:
    """Подтверждение отзыва аккаунта."""
    return [[
        Button.inline("✅ Да, отозвать", data=f"issue:confirm_revoke:{issue_id}"),
        Button.inline("❌ Нет", data="nav:active"),
    ]]


def confirm_delete_account(account_id: int) -> List[List[Button]]:
    """Подтверждение удаления аккаунта."""
    return [[
        Button.inline("✅ Да, удалить", data=f"acc:confirm_delete:{account_id}"),
        Button.inline("❌ Нет", data=f"acc:detail:{account_id}"),
    ]]


def issue_detail_buttons(issue_id: int, status: str, has_account: bool = False) -> List[List[Button]]:
    """Кнопки в деталях заявки в зависимости от статуса."""
    buttons = []
    
    if status == "approved":
        if has_account:
            buttons.append([
                Button.inline("💾 Session", data=f"issue:download_session:{issue_id}"),
                Button.inline("📦 TData", data=f"issue:download_tdata:{issue_id}"),
            ])
            buttons.append([
                Button.inline("🔑 Код", data=f"issue:request_code:{issue_id}"),
                Button.inline("🔒 Отозвать", data=f"issue:revoke:{issue_id}"),
            ])
        else:
            buttons.append([Button.inline("🔒 Отозвать", data=f"issue:revoke:{issue_id}")])
    elif status == "pending":
        buttons.append([
            Button.inline("✅ Подтвердить", data=f"issue:approve:{issue_id}"),
            Button.inline("❌ Отклонить", data=f"issue:reject:{issue_id}"),
        ])
    
    buttons.append([Button.inline("⬅️ Назад", data="nav:main")])
    return buttons


# ============================================================
# ЭКРАНЫ МЕНЕДЖЕРА
# ============================================================

def manager_request_sent() -> List[List[Button]]:
    """Кнопки после отправки заявки менеджером."""
    return [
        [Button.inline("⬅️ В меню", data=CB.MGR_MENU)],
    ]


def manager_limit_reached() -> List[List[Button]]:
    """Кнопки при достижении лимита аккаунтов."""
    return [
        [Button.inline("⬅️ В меню", data=CB.MGR_MENU)],
    ]


def manager_account_issued(can_request_more: bool = True) -> List[List[Button]]:
    """Кнопки после получения аккаунта."""
    return [
        [
            Button.inline("🔄 Код ещё раз", data=CB.MGR_WAIT_CODE_AGAIN),
            Button.inline("⬅️ В меню", data=CB.MGR_MENU),
        ],
    ]


def manager_code_received() -> List[List[Button]]:
    """Кнопки после получения кода."""
    return [
        [
            Button.inline("🔄 Код ещё раз", data=CB.MGR_WAIT_CODE_AGAIN),
            Button.inline("⬅️ В меню", data=CB.MGR_MENU),
        ],
    ]


def manager_code_timeout() -> List[List[Button]]:
    """Кнопки при таймауте кода."""
    return [
        [
            Button.inline("🔄 Ещё раз", data=CB.MGR_WAIT_CODE_AGAIN),
            Button.inline("⬅️ Меню", data=CB.MGR_MENU),
        ],
    ]


def manager_my_accounts_list(issues: list, can_request_more: bool = True) -> List[List[Button]]:
    """Список активных аккаунтов менеджера."""
    buttons = []
    if can_request_more:
        buttons.append([Button.inline("🧾 Получить ещё", data=CB.MGR_GET)])
    buttons.append([Button.inline("⬅️ В меню", data=CB.MGR_MENU)])
    return buttons


def manager_my_accounts_empty() -> List[List[Button]]:
    """Кнопки когда нет активных аккаунтов."""
    return [
        [Button.inline("🧾 Получить аккаунт", data=CB.MGR_GET)],
    ]


def manager_history_list(
    issues: list,
    page: int = 0,
    per_page: int = 5
) -> List[List[Button]]:
    """История выдач менеджера с пагинацией."""
    buttons = []
    total_pages = max(1, (len(issues) + per_page - 1) // per_page)
    
    # Пагинация
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"{CB.MGR_HISTORY}:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"{CB.MGR_HISTORY}:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ В меню", data=CB.MGR_MENU)])
    return buttons


def manager_history_empty() -> List[List[Button]]:
    """Кнопки когда история пуста."""
    return [
        [Button.inline("🧾 Получить аккаунт", data=CB.MGR_GET)],
    ]


def manager_help() -> List[List[Button]]:
    """Кнопки в разделе помощи."""
    return [
        [Button.inline("🧾 Получить аккаунт", data=CB.MGR_GET)],
    ]


# ============================================================
# ПРОКСИ
# ============================================================

def admin_proxies_menu(stats: dict) -> List[List[Button]]:
    """Главное меню прокси."""
    return [
        [
            Button.inline("📋 Список", data=CB.PROXY_LIST),
            Button.inline("➕ Добавить", data=CB.PROXY_ADD),
        ],
        [
            Button.inline("🔄 Проверить", data=CB.PROXY_CHECK_ALL),
            Button.inline("⬅️ Назад", data="nav:main"),
        ],
    ]


def admin_proxies_list(
    proxies: list,
    page: int = 0,
    per_page: int = 8
) -> List[List[Button]]:
    """Список прокси с пагинацией."""
    from services import proxy_service
    
    buttons = []
    
    start = page * per_page
    end = start + per_page
    page_proxies = proxies[start:end]
    total_pages = max(1, (len(proxies) + per_page - 1) // per_page)
    
    for proxy in page_proxies:
        status = "🟢" if proxy.is_active else "🔴"
        latency = f"{proxy.latency_ms}ms" if proxy.latency_ms else "?"
        flag = proxy_service.get_country_flag(proxy.country)
        label = f"{status} {flag} {proxy.host}:{proxy.port} [{latency}]"
        buttons.append([Button.inline(label, data=f"{CB.PROXY_DETAIL}:{proxy.id}")])
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"proxy:page:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"proxy:page:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ Назад", data="nav:proxies")])
    return buttons


def admin_proxy_detail(proxy, accounts_count: int) -> List[List[Button]]:
    """Детали прокси с действиями."""
    toggle_text = "🔴 Откл." if proxy.is_active else "🟢 Вкл."
    
    buttons = [
        [
            Button.inline("🔍 Проверить", data=f"{CB.PROXY_CHECK_ONE}:{proxy.id}"),
            Button.inline(toggle_text, data=f"{CB.PROXY_TOGGLE}:{proxy.id}"),
        ],
        [
            Button.inline("🗑 Удалить", data=f"{CB.PROXY_DELETE}:{proxy.id}"),
            Button.inline("⬅️ Назад", data=CB.PROXY_LIST),
        ],
    ]
    return buttons


def confirm_delete_proxy(proxy_id: int) -> List[List[Button]]:
    """Подтверждение удаления прокси."""
    return [
        [
            Button.inline("✅ Да", data=f"{CB.PROXY_CONFIRM_DELETE}:{proxy_id}"),
            Button.inline("❌ Нет", data=f"{CB.PROXY_DETAIL}:{proxy_id}"),
        ]
    ]


def admin_add_proxy_result(success: bool = True) -> List[List[Button]]:
    """Кнопки после добавления прокси."""
    return [
        [
            Button.inline("➕ Ещё", data=CB.PROXY_ADD),
            Button.inline("⬅️ Меню", data="nav:main"),
        ],
    ]


# ============================================================
# МЕНЕДЖЕРЫ (для админа)
# ============================================================

def admin_managers_list(
    managers: list,
    page: int = 0,
    per_page: int = 8
) -> List[List[Button]]:
    """Список менеджеров с активными аккаунтами."""
    buttons = []
    
    start = page * per_page
    end = start + per_page
    page_managers = managers[start:end]
    total_pages = max(1, (len(managers) + per_page - 1) // per_page)
    
    for mgr in page_managers:
        username = f"@{mgr['username']}" if mgr.get('username') else f"ID:{mgr['tg_id']}"
        count = mgr.get('accounts_count', 0)
        label = f"👤 {username} • {count} акк."
        buttons.append([Button.inline(label, data=f"{CB.MGR_DETAIL}:{mgr['user_id']}")])
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("◀️", data=f"mgr_admin:page:{page - 1}"))
        nav_row.append(Button.inline(f"{page + 1}/{total_pages}", data=CB.NOOP))
        if page < total_pages - 1:
            nav_row.append(Button.inline("▶️", data=f"mgr_admin:page:{page + 1}"))
        buttons.append(nav_row)
    
    buttons.append([Button.inline("⬅️ Назад", data="nav:main")])
    return buttons


def admin_manager_detail(user_id: int, issues: list) -> List[List[Button]]:
    """Детали менеджера с его аккаунтами."""
    buttons = []
    
    # Показываем аккаунты с кнопками отзыва
    for issue in issues[:10]:  # Макс 10 аккаунтов
        acc = issue.account
        if acc:
            phone = acc.phone or f"#{acc.id}"
            premium = "⭐" if acc.is_premium else ""
            buttons.append([
                Button.inline(f"{phone} {premium}".strip(), data=f"issue:detail:{issue.id}"),
                Button.inline("🔒", data=f"{CB.MGR_REVOKE_ONE}:{issue.id}"),
            ])
    
    if issues:
        buttons.append([
            Button.inline("🔒 Отозвать все", data=f"{CB.MGR_REVOKE_ALL}:{user_id}"),
            Button.inline("⬅️ Назад", data="nav:managers"),
        ])
    else:
        buttons.append([Button.inline("⬅️ Назад", data="nav:managers")])
    
    return buttons


def confirm_revoke_all(user_id: int, count: int) -> List[List[Button]]:
    """Подтверждение отзыва всех аккаунтов у менеджера."""
    return [
        [
            Button.inline(f"✅ Да ({count})", data=f"{CB.MGR_CONFIRM_REVOKE_ALL}:{user_id}"),
            Button.inline("❌ Нет", data=f"{CB.MGR_DETAIL}:{user_id}"),
        ]
    ]


# ============================================================
# УТИЛИТЫ
# ============================================================

def back_button(destination: str = "nav:main") -> List[List[Button]]:
    """Универсальная кнопка Назад."""
    return [[Button.inline("⬅️ Назад", data=destination)]]


def close_button() -> List[List[Button]]:
    """Кнопка закрытия сообщения."""
    return [[Button.inline("✖️ Закрыть", data=CB.CLOSE)]]


# ============================================================
# LEGACY COMPATIBILITY
# ============================================================

def approve_reject_keyboard(issue_id: int) -> List[List[Button]]:
    """Legacy: кнопки подтверждения/отклонения."""
    return admin_issue_card(issue_id)


def revoke_keyboard(issue_id: int) -> List[List[Button]]:
    """Legacy: кнопка отзыва."""
    return [[Button.inline("🔴 Отозвать", data=f"issue:revoke:{issue_id}")]]
