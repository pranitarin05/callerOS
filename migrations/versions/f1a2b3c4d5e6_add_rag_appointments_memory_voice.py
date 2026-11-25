"""add rag, appointments, memory and voice fields

Revision ID: f1a2b3c4d5e6
Revises: d0fd1ed2b278
Create Date: 2026-11-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "d0fd1ed2b278"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("leads") as batch:
        batch.add_column(
            sa.Column(
                "preferred_language",
                sa.String(),
                nullable=False,
                server_default="auto",
            )
        )
        batch.add_column(sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("calls") as batch:
        batch.add_column(sa.Column("language", sa.String(), nullable=True))
        batch.add_column(
            sa.Column(
                "channel",
                sa.String(),
                nullable=False,
                server_default="outbound",
            )
        )

    with op.batch_alter_table("knowledge_documents") as batch:
        batch.add_column(
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default="pending",
            )
        )
        batch.add_column(sa.Column("mime_type", sa.String(), nullable=True))
        batch.add_column(
            sa.Column(
                "char_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "chunk_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(sa.Column("error", sa.Text(), nullable=True))

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=36),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_chunks_id", "knowledge_chunks", ["id"], unique=False)
    op.create_index(
        "ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"], unique=False
    )
    op.create_index(
        "ix_knowledge_chunks_owner_id", "knowledge_chunks", ["owner_id"], unique=False
    )

    op.create_table(
        "lead_memories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "lead_id",
            sa.String(length=36),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_facts", sa.Text(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_memories_id", "lead_memories", ["id"], unique=False)
    op.create_index(
        "ix_lead_memories_lead_id", "lead_memories", ["lead_id"], unique=True
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "lead_id",
            sa.String(length=36),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
        sa.Column("title", sa.String(), nullable=False, server_default="Product demo"),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "call_id",
            sa.String(length=36),
            sa.ForeignKey("calls.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_appointments_id", "appointments", ["id"], unique=False)
    op.create_index("ix_appointments_lead_id", "appointments", ["lead_id"], unique=False)
    op.create_index("ix_appointments_user_id", "appointments", ["user_id"], unique=False)
    op.create_index(
        "ix_appointments_scheduled_at", "appointments", ["scheduled_at"], unique=False
    )
    op.create_index("ix_appointments_status", "appointments", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
    op.drop_index("ix_appointments_user_id", table_name="appointments")
    op.drop_index("ix_appointments_lead_id", table_name="appointments")
    op.drop_index("ix_appointments_id", table_name="appointments")
    op.drop_table("appointments")

    op.drop_index("ix_lead_memories_lead_id", table_name="lead_memories")
    op.drop_index("ix_lead_memories_id", table_name="lead_memories")
    op.drop_table("lead_memories")

    op.drop_index("ix_knowledge_chunks_owner_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_document_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    with op.batch_alter_table("knowledge_documents") as batch:
        batch.drop_column("error")
        batch.drop_column("chunk_count")
        batch.drop_column("char_count")
        batch.drop_column("mime_type")
        batch.drop_column("status")

    with op.batch_alter_table("calls") as batch:
        batch.drop_column("channel")
        batch.drop_column("language")

    with op.batch_alter_table("leads") as batch:
        batch.drop_column("last_contact_at")
        batch.drop_column("preferred_language")
