"""Initial tables: users, accounts, issues, proxies

Revision ID: 000_initial
Revises: (none)
Create Date: 2024-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""
    
    # === PROXIES ===
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
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('fail_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_accounts', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_proxies_is_active', 'proxies', ['is_active'])
    
    # === USERS ===
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tg_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='manager'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_users_tg_id', 'users', ['tg_id'])
    
    # === ACCOUNTS ===
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        # Telegram user info
        sa.Column('tg_user_id', sa.BigInteger(), nullable=True, unique=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        # API credentials
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('api_hash', sa.String(64), nullable=True),
        # Device fingerprint
        sa.Column('device_model', sa.String(255), nullable=True),
        sa.Column('system_version', sa.String(255), nullable=True),
        sa.Column('app_version', sa.String(255), nullable=True),
        sa.Column('lang_code', sa.String(10), nullable=True),
        sa.Column('system_lang_code', sa.String(10), nullable=True),
        # Storage
        sa.Column('storage_type', sa.String(50), nullable=False, server_default='telethon_session'),
        sa.Column('session_path', sa.String(512), nullable=True),
        sa.Column('tdata_path', sa.String(512), nullable=True),
        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default='free'),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        # Error tracking
        sa.Column('error_text', sa.Text(), nullable=True),
        # Proxy FK
        sa.Column('proxy_id', sa.Integer(), sa.ForeignKey('proxies.id'), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_accounts_tg_user_id', 'accounts', ['tg_user_id'])
    op.create_index('ix_accounts_phone', 'accounts', ['phone'])
    op.create_index('ix_accounts_status', 'accounts', ['status'])
    op.create_index('ix_accounts_proxy_id', 'accounts', ['proxy_id'])
    
    # === ISSUES ===
    op.create_table(
        'issues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        # Timestamps
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        # Other fields
        sa.Column('confirmation_code', sa.String(10), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('account_was_premium', sa.Boolean(), nullable=True),
    )
    op.create_index('ix_issues_user_id', 'issues', ['user_id'])
    op.create_index('ix_issues_account_id', 'issues', ['account_id'])
    op.create_index('ix_issues_status', 'issues', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('issues')
    op.drop_table('accounts')
    op.drop_table('users')
    op.drop_table('proxies')
