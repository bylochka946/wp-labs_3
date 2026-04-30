"""add owner_id to items table

Revision ID: 003
Revises: 002
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавление поля owner_id в таблицу items"""
    # Сначала добавляем колонку как nullable
    op.add_column('items', sa.Column('owner_id', UUID(as_uuid=True), nullable=True))
    
    # Создаем foreign key constraint
    op.create_foreign_key(
        'fk_items_owner_id_users',
        'items', 'users',
        ['owner_id'], ['id']
    )
    
    # Создаем индекс для производительности
    op.create_index('ix_items_owner_id', 'items', ['owner_id'])
    
    op.alter_column('items', 'owner_id', nullable=False)


def downgrade() -> None:
    """Откат миграции - удаление поля owner_id"""
    op.drop_index('ix_items_owner_id')
    op.drop_constraint('fk_items_owner_id_users', 'items', type_='foreignkey')
    op.drop_column('items', 'owner_id')
