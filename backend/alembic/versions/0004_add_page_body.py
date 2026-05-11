"""add page_body to links

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "links",
        sa.Column("page_body", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("links", "page_body")
