"""add run_files, run_metrics, run_splits, run_track

Revision ID: c4a8d7b1e7d3
Revises: b3f5c8a3b2a2
Create Date: 2025-11-26 00:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4a8d7b1e7d3'
down_revision: Union[str, Sequence[str], None] = 'b3f5c8a3b2a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'run_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_run_files_id', 'run_files', ['id'])
    op.create_index('ix_run_files_run_id', 'run_files', ['run_id'])

    op.create_table(
        'run_metrics',
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('avg_hr', sa.Integer(), nullable=True),
        sa.Column('max_hr', sa.Integer(), nullable=True),
        sa.Column('elev_gain_ft', sa.Numeric(7, 1), nullable=True),
        sa.Column('elev_loss_ft', sa.Numeric(7, 1), nullable=True),
        sa.Column('moving_time_sec', sa.Integer(), nullable=True),
        sa.Column('device', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('run_id')
    )

    op.create_table(
        'run_splits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False),
        sa.Column('distance_mi', sa.Numeric(6, 3), nullable=False),
        sa.Column('duration_sec', sa.Integer(), nullable=False),
        sa.Column('avg_hr', sa.Integer(), nullable=True),
        sa.Column('max_hr', sa.Integer(), nullable=True),
        sa.Column('elev_gain_ft', sa.Numeric(7, 1), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_run_splits_id', 'run_splits', ['id'])
    op.create_index('ix_run_splits_run_id', 'run_splits', ['run_id'])

    op.create_table(
        'run_track',
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('geojson', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('bounds', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('points_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('run_id')
    )


def downgrade() -> None:
    op.drop_table('run_track')
    op.drop_index('ix_run_splits_run_id', table_name='run_splits')
    op.drop_index('ix_run_splits_id', table_name='run_splits')
    op.drop_table('run_splits')
    op.drop_table('run_metrics')
    op.drop_index('ix_run_files_run_id', table_name='run_files')
    op.drop_index('ix_run_files_id', table_name='run_files')
    op.drop_table('run_files')

