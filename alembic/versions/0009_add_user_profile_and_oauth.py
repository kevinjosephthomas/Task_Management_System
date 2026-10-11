"""add username, profile fields, and OAuth columns to users

Revision ID: 0009
Revises: 0008
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("username", sa.String(100), nullable=True, unique=True))
    op.add_column("users", sa.Column("full_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("profile_picture_url", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True, unique=True))
    op.add_column("users", sa.Column("oauth_provider", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("users", "oauth_provider")
    op.drop_column("users", "google_id")
    op.drop_column("users", "profile_picture_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "full_name")
    op.drop_column("users", "username")
