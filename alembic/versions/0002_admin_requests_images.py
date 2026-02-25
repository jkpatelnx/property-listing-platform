"""Add role to users, image_filename to properties, create contact_requests table.

Revision ID: 0002
Revises: 0001
Create Date: 2025-02-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users: add role column ─────────────────────────────────────────────────
    op.add_column(
        "users",
        sa.Column("role", sa.String(10), nullable=False, server_default="user"),
    )

    # ── properties: add image_filename column ──────────────────────────────────
    op.add_column(
        "properties",
        sa.Column("image_filename", sa.String(255), nullable=True),
    )

    # ── contact_requests table ─────────────────────────────────────────────────
    op.create_table(
        "contact_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_contact_requests_id", "contact_requests", ["id"])
    op.create_index("ix_contact_requests_property_id", "contact_requests", ["property_id"])


def downgrade() -> None:
    op.drop_table("contact_requests")
    op.drop_column("properties", "image_filename")
    op.drop_column("users", "role")
