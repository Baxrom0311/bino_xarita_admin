"""add kiosks table

Revision ID: 8b1f2a3c4d5e
Revises: 2c420301e271
Create Date: 2026-01-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b1f2a3c4d5e'
down_revision: Union[str, Sequence[str], None] = '2c420301e271'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'kiosks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('floor_id', sa.Integer(), nullable=False),
        sa.Column('waypoint_id', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['floor_id'], ['floors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['waypoint_id'], ['waypoints.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kiosks_id'), 'kiosks', ['id'], unique=False)
    op.create_index(op.f('ix_kiosks_floor_id'), 'kiosks', ['floor_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_kiosks_floor_id'), table_name='kiosks')
    op.drop_index(op.f('ix_kiosks_id'), table_name='kiosks')
    op.drop_table('kiosks')
