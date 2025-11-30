"""add distance-indexed series columns

Revision ID: efc2a7a1b8f2
Revises: da7f1e2c9af0
Create Date: 2025-11-26 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'efc2a7a1b8f2'
down_revision: Union[str, Sequence[str], None] = 'da7f1e2c9af0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('run_metrics', sa.Column('hr_dist_series', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('run_metrics', sa.Column('pace_dist_series', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('run_metrics', sa.Column('elev_dist_series', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('run_metrics', 'elev_dist_series')
    op.drop_column('run_metrics', 'pace_dist_series')
    op.drop_column('run_metrics', 'hr_dist_series')

