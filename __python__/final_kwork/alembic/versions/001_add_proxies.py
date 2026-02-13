"""Add proxies table and proxy_id to accounts

Revision ID: 001_add_proxies
Revises: 
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '001_add_proxies'
down_revision: Union[str, None] = '000_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name):
    """Проверить существование таблицы."""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name, column_name):
    """Проверить существование колонки."""
    inspector = inspect(conn)
    # Сначала проверяем существование таблицы
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()
    
    # Создаём таблицу proxies если её нет
    if not table_exists(conn, 'proxies'):
        op.create_table(
            'proxies',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('proxy_type', sa.String(20), nullable=False, server_default='http'),
            sa.Column('host', sa.String(255), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(255), nullable=True),
            sa.Column('password', sa.String(255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('last_checked_at', sa.DateTime(), nullable=True),
            sa.Column('last_check_ip', sa.String(45), nullable=True),
            sa.Column('latency_ms', sa.Integer(), nullable=True),
            sa.Column('fail_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('max_accounts', sa.Integer(), nullable=False, server_default='6'),
            sa.Column('comment', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_proxies_is_active', 'proxies', ['is_active'])
    
    # Добавляем колонку proxy_id в accounts если таблица существует и колонки нет
    if table_exists(conn, 'accounts') and not column_exists(conn, 'accounts', 'proxy_id'):
        op.add_column('accounts', sa.Column('proxy_id', sa.Integer(), nullable=True))
        
        # SQLite не поддерживает добавление FK на существующую таблицу напрямую
        # Создаём только индекс
        op.create_index('ix_accounts_proxy_id', 'accounts', ['proxy_id'])


def downgrade() -> None:
    # Удаляем FK и индекс
    op.drop_constraint('fk_accounts_proxy_id', 'accounts', type_='foreignkey')
    op.drop_index('ix_accounts_proxy_id', 'accounts')
    
    # Удаляем колонку
    op.drop_column('accounts', 'proxy_id')
    
    # Удаляем таблицу proxies
    op.drop_index('ix_proxies_is_active', 'proxies')
    op.drop_table('proxies')
