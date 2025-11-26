"""add start_time to run

Revision ID: 7b9d1cf2a1f1
Revises: a16f284ad61c
Create Date: 2025-11-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b9d1cf2a1f1'
down_revision: Union[str, Sequence[str], None] = 'a16f284ad61c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('runs', sa.Column('start_time', sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column('runs', 'start_time')

