"""replace vapi with elevenlabs exotel

Revision ID: d0fd1ed2b278
Revises: 50351dd772d9
Create Date: 2026-11-24 14:28:15.118280

"""
from alembic import op
import sqlalchemy as sa


revision = "d0fd1ed2b278"
down_revision = "50351dd772d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("calls") as batch:
        batch.add_column(
            sa.Column(
                "provider",
                sa.String(),
                nullable=False,
                server_default="elevenlabs_exotel",
            )
        )
        batch.add_column(sa.Column("conversation_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("exotel_call_sid", sa.String(length=128), nullable=True))
        batch.add_column(
            sa.Column(
                "initiation_status",
                sa.String(),
                nullable=False,
                server_default="submitted",
            )
        )
        batch.add_column(sa.Column("call_outcome", sa.String(), nullable=True))
        batch.add_column(sa.Column("qualification_json", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column(
                "followup_required",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(sa.Column("error_message", sa.Text(), nullable=True))
        batch.drop_index("ix_calls_vapi_call_id")
        batch.create_index("ix_calls_conversation_id", ["conversation_id"], unique=True)
        batch.create_index("ix_calls_exotel_call_sid", ["exotel_call_sid"], unique=True)
        batch.drop_column("vapi_call_id")


def downgrade():
    with op.batch_alter_table("calls") as batch:
        batch.add_column(sa.Column("vapi_call_id", sa.String(), nullable=True))
        batch.drop_index("ix_calls_exotel_call_sid")
        batch.drop_index("ix_calls_conversation_id")
        batch.create_index("ix_calls_vapi_call_id", ["vapi_call_id"], unique=True)
        batch.drop_column("error_message")
        batch.drop_column("followup_required")
        batch.drop_column("qualification_json")
        batch.drop_column("call_outcome")
        batch.drop_column("initiation_status")
        batch.drop_column("exotel_call_sid")
        batch.drop_column("conversation_id")
        batch.drop_column("provider")
