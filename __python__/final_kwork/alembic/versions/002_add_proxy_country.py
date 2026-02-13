"""Add country column to proxies table

Revision ID: 002_add_proxy_country
Revises: 001_add_proxies
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '002_add_proxy_country'
down_revision: Union[str, None] = '001_add_proxies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name):
    """Проверить существование таблицы."""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name, column_name):
    """Проверить существование колонки."""
    inspector = inspect(conn)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()
    
    # Добавляем колонку country если таблица proxies существует и колонки нет
    if table_exists(conn, 'proxies') and not column_exists(conn, 'proxies', 'country'):
        op.add_column('proxies', sa.Column('country', sa.String(2), nullable=True))


def downgrade() -> None:
    op.drop_column('proxies', 'country')
