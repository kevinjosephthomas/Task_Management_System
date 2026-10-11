"""add due_datetime to tasks and timezone to users

Revision ID: 0010
Revises: 0009
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("due_datetime", sa.TIMESTAMP(), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(50), nullable=True, server_default=sa.text("'UTC'")))


def downgrade():
    op.drop_column("users", "timezone")
    op.drop_column("tasks", "due_datetime")
