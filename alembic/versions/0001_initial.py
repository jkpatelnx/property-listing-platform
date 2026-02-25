"""Initial migration – create users and properties tables.

Revision ID: 0001
Revises:
Create Date: 2025-02-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_id", "users", ["id"])

    # ── properties ─────────────────────────────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bathrooms", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("property_type", sa.String(50), nullable=False, server_default="apartment"),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_properties_id", "properties", ["id"])
    op.create_index("ix_properties_city", "properties", ["city"])


def downgrade() -> None:
    op.drop_table("properties")
    op.drop_table("users")
