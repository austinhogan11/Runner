"""add hr_series and pace_series and hr_zones to run_metrics

Revision ID: da7f1e2c9af0
Revises: c4a8d7b1e7d3
Create Date: 2025-11-26 01:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'da7f1e2c9af0'
down_revision: Union[str, Sequence[str], None] = 'c4a8d7b1e7d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('run_metrics', sa.Column('hr_zones', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('run_metrics', sa.Column('hr_series', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('run_metrics', sa.Column('pace_series', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('run_metrics', 'pace_series')
    op.drop_column('run_metrics', 'hr_series')
    op.drop_column('run_metrics', 'hr_zones')

