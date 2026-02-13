"""add device fingerprint fields

Revision ID: 005_add_device_fingerprint
Revises: 004_update_max_accounts
Create Date: 2025-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_device_fingerprint'
down_revision: Union[str, None] = '004_update_max_accounts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Проверить существует ли колонка в таблице (SQLite)."""
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Проверить существует ли таблица (SQLite)."""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    ))
    return result.fetchone() is not None


def upgrade() -> None:
    """Add device fingerprint fields to accounts table."""
    # Проверяем существование таблицы (миграция 000_initial должна её создать)
    if not table_exists('accounts'):
        return
    
    # Проверяем каждую колонку перед добавлением (для идемпотентности)
    if not column_exists('accounts', 'device_model'):
        op.add_column('accounts', sa.Column('device_model', sa.String(255), nullable=True))
    
    if not column_exists('accounts', 'system_version'):
        op.add_column('accounts', sa.Column('system_version', sa.String(255), nullable=True))
    
    if not column_exists('accounts', 'app_version'):
        op.add_column('accounts', sa.Column('app_version', sa.String(255), nullable=True))
    
    if not column_exists('accounts', 'lang_code'):
        op.add_column('accounts', sa.Column('lang_code', sa.String(10), nullable=True))
    
    if not column_exists('accounts', 'system_lang_code'):
        op.add_column('accounts', sa.Column('system_lang_code', sa.String(10), nullable=True))


def downgrade() -> None:
    """Remove device fingerprint fields from accounts table."""
    # SQLite не поддерживает DROP COLUMN напрямую в старых версиях
    # Но современные версии (3.35+) поддерживают
    if column_exists('accounts', 'system_lang_code'):
        op.drop_column('accounts', 'system_lang_code')
    if column_exists('accounts', 'lang_code'):
        op.drop_column('accounts', 'lang_code')
    if column_exists('accounts', 'app_version'):
        op.drop_column('accounts', 'app_version')
    if column_exists('accounts', 'system_version'):
        op.drop_column('accounts', 'system_version')
    if column_exists('accounts', 'device_model'):
        op.drop_column('accounts', 'device_model')
