"""Add helpdesk tickets table

Revision ID: 0007_helpdesk_tickets
Revises: 0006_kiosks
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_helpdesk_tickets"
down_revision = "0006_kiosks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "helpdesk_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
        ),
        sa.Column("requester_name", sa.String(length=120)),
        sa.Column("requester_email", sa.String(length=255)),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'open'")),
        sa.Column("priority", sa.String(length=30), nullable=False, server_default=sa.text("'normal'")),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_helpdesk_tickets_tenant_id", "helpdesk_tickets", ["tenant_id"])
    op.create_index("ix_helpdesk_tickets_status", "helpdesk_tickets", ["status"])
    op.create_index("ix_helpdesk_tickets_priority", "helpdesk_tickets", ["priority"])


def downgrade() -> None:
    op.drop_index("ix_helpdesk_tickets_priority", table_name="helpdesk_tickets")
    op.drop_index("ix_helpdesk_tickets_status", table_name="helpdesk_tickets")
    op.drop_index("ix_helpdesk_tickets_tenant_id", table_name="helpdesk_tickets")
    op.drop_table("helpdesk_tickets")
