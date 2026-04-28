"""app_settings table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("embedding_provider", sa.Text(), nullable=False),
        sa.Column("openai_api_key", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO app_settings (id, embedding_provider) VALUES (1, 'local')")


def downgrade() -> None:
    op.drop_table("app_settings")
