"""
Модели БД: User, Account, Issue, Proxy.
"""
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class ProxyType(str, enum.Enum):
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
    HTTP = "http"
    HTTPS = "https"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class AccountStatus(str, enum.Enum):
    FREE = "free"                   # Свободен для выдачи
    # Совместимость: в некоторых версиях использовался промежуточный статус RESERVED.
    RESERVED = "reserved"
    ASSIGNED = "assigned"           # Выдан менеджеру
    DISABLED = "disabled"           # Отключён / проблемный
    NEEDS_CONVERSION = "needs_conversion"  # tdata требует конвертации


class StorageType(str, enum.Enum):
    TELETHON_SESSION = "telethon_session"  # .session файл
    TDATA = "tdata"                        # Telegram Desktop tdata


class IssueStatus(str, enum.Enum):
    PENDING = "pending"     # Ожидает подтверждения админа
    APPROVED = "approved"   # Одобрен, аккаунт выдан
    # Совместимость: старые обработчики могут ссылаться на CODE_WAIT.
    CODE_WAIT = "code_wait"
    REJECTED = "rejected"   # Отклонён админом
    REVOKED = "revoked"     # Отозван админом


class Proxy(Base):
    """Прокси-серверы для аккаунтов."""
    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Параметры подключения
    proxy_type: Mapped[ProxyType] = mapped_column(
        Enum(ProxyType, values_callable=lambda x: [e.value for e in x]), 
        default=ProxyType.HTTP
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Статус и метрики
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_check_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Лимит аккаунтов на прокси (0 = без лимита)
    max_accounts: Mapped[int] = mapped_column(Integer, default=6)
    
    # Комментарий от админа
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="proxy")
    
    def __repr__(self) -> str:
        auth = f"{self.username}:***@" if self.username else ""
        return f"Proxy({self.proxy_type.value}://{auth}{self.host}:{self.port})"
    
    @property
    def display_string(self) -> str:
        """Строка для отображения (без пароля)."""
        auth = f"{self.username}:***@" if self.username else ""
        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"
    
    def to_telethon_dict(self) -> dict:
        """Конвертация в формат для Telethon."""
        proxy_dict = {
            'proxy_type': self.proxy_type.value,
            'addr': self.host,
            'port': self.port,
        }
        if self.username:
            proxy_dict['username'] = self.username
        if self.password:
            proxy_dict['password'] = self.password
        return proxy_dict


class User(Base):
    """Пользователи бота (менеджеры и админы)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MANAGER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="user")


class Account(Base):
    """Telegram-аккаунты для выдачи."""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Telegram user info (получаем при валидации сессии)
    tg_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    
    # API credentials (если специфичные для аккаунта)
    api_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    api_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Device fingerprint (для стабильности сессии)
    device_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lang_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    system_lang_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Storage info
    storage_type: Mapped[StorageType] = mapped_column(
        Enum(StorageType, values_callable=lambda x: [e.value for e in x]), 
        default=StorageType.TELETHON_SESSION
    )
    session_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    tdata_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Status
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, values_callable=lambda x: [e.value for e in x]), 
        default=AccountStatus.FREE, index=True
    )
    is_premium: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Error tracking
    error_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Proxy (опционально)
    proxy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("proxies.id"), nullable=True, index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    proxy: Mapped[Optional["Proxy"]] = relationship("Proxy", back_populates="accounts")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="account")


class Issue(Base):
    """Заявки на выдачу аккаунтов."""
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    account_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True, index=True
    )
    
    status: Mapped[IssueStatus] = mapped_column(
        Enum(IssueStatus), default=IssueStatus.PENDING, index=True
    )
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Код подтверждения (если перехвачен)
    confirmation_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # IP-адрес (заглушка для будущего)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Risk score от AI
    risk_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Снимок premium статуса на момент выдачи
    account_was_premium: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="issues")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="issues")
