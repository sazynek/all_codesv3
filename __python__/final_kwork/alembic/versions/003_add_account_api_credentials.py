"""Add api_id and api_hash to accounts

Revision ID: 003_add_api_credentials
Revises: 002_add_proxy_country
Create Date: 2025-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '003_add_api_credentials'
down_revision: Union[str, None] = '002_add_proxy_country'
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
    
    # Добавляем поля api_id и api_hash в таблицу accounts если она существует
    if not table_exists(conn, 'accounts'):
        return
    
    if not column_exists(conn, 'accounts', 'api_id'):
        with op.batch_alter_table('accounts', schema=None) as batch_op:
            batch_op.add_column(sa.Column('api_id', sa.Integer(), nullable=True))
    
    if not column_exists(conn, 'accounts', 'api_hash'):
        with op.batch_alter_table('accounts', schema=None) as batch_op:
            batch_op.add_column(sa.Column('api_hash', sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.drop_column('api_hash')
        batch_op.drop_column('api_id')
