"""create users and tokens tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создание таблицы users"""
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String, unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String, nullable=True),
        sa.Column('password_salt', sa.String, nullable=True),
        sa.Column('yandex_id', sa.String, unique=True, nullable=True, index=True),
        sa.Column('vk_id', sa.String, unique=True, nullable=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True)
    )
    
    """Создание таблицы tokens"""
    op.create_table(
        'tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('token_hash', sa.String, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('revoked', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )


def downgrade() -> None:
    """Откат миграции - удаление таблиц"""
    op.drop_table('tokens')
    op.drop_table('users')
