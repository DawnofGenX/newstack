"""add status column

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-02 00:00:00

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
    )


def downgrade() -> None:
    op.drop_column("items", "status")
