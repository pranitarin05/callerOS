"""add agent script overrides

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-11-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("agent_configs") as batch:
        batch.add_column(sa.Column("first_message", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column(
                "language",
                sa.String(),
                nullable=False,
                server_default="auto",
            )
        )


def downgrade():
    with op.batch_alter_table("agent_configs") as batch:
        batch.drop_column("language")
        batch.drop_column("first_message")
