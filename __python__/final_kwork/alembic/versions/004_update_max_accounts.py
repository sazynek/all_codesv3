"""Update max_accounts default to 6

Revision ID: 004_update_max_accounts
Revises: 003_add_api_credentials
Create Date: 2025-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '004_update_max_accounts'
down_revision: Union[str, None] = '003_add_api_credentials'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name):
    """Проверить существование таблицы."""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Изменяем значение по умолчанию для max_accounts с 5 на 6."""
    conn = op.get_bind()
    
    # Проверяем существование таблицы proxies
    if not table_exists(conn, 'proxies'):
        return
    
    # SQLite не поддерживает ALTER COLUMN напрямую
    # Используем batch operations
    with op.batch_alter_table('proxies') as batch_op:
        batch_op.alter_column(
            'max_accounts',
            existing_type=sa.Integer(),
            nullable=False,
            server_default='6'
        )


def downgrade() -> None:
    """Возвращаем значение по умолчанию обратно на 5."""
    with op.batch_alter_table('proxies') as batch_op:
        batch_op.alter_column(
            'max_accounts',
            existing_type=sa.Integer(),
            nullable=False,
            server_default='5'
        )
