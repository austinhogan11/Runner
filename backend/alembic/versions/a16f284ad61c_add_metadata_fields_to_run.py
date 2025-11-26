"""Add metadata fields to Run

Revision ID: a16f284ad61c
Revises: 
Create Date: 2025-11-24 21:45:11.450183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a16f284ad61c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Instead of dropping the runs table, add the new metadata columns
    to the existing runs table.
    """
    # Add run_type and source for categorization and provenance
    op.add_column(
        "runs",
        sa.Column(
            "run_type",
            sa.String(length=20),
            nullable=False,
            server_default="easy",
        ),
    )
    op.add_column(
        "runs",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default="manual",
        ),
    )

    # Add timestamps for creation and update tracking
    op.add_column(
        "runs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "runs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema.

    Remove the metadata columns added in upgrade().
    """
    op.drop_column("runs", "updated_at")
    op.drop_column("runs", "created_at")
    op.drop_column("runs", "source")
    op.drop_column("runs", "run_type")
