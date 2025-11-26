"""add weekly_goals table

Revision ID: b3f5c8a3b2a2
Revises: 7b9d1cf2a1f1
Create Date: 2025-11-26 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f5c8a3b2a2'
down_revision: Union[str, Sequence[str], None] = '7b9d1cf2a1f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if 'weekly_goals' not in tables:
        op.create_table(
            'weekly_goals',
            sa.Column('week_start', sa.Date(), primary_key=True, nullable=False),
            sa.Column('goal_miles', sa.Numeric(5, 2), nullable=False),
            sa.Column('notes', sa.String(), nullable=True),
        )


def downgrade() -> None:
    # Safe drop if exists
    op.execute('DROP TABLE IF EXISTS weekly_goals')
