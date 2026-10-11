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
    # SQLite requires batch mode for unique columns
    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("full_name", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("bio", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("profile_picture_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("google_id", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("oauth_provider", sa.String(50), nullable=True))
        batch_op.create_unique_constraint("uq_users_username", ["username"])
        batch_op.create_unique_constraint("uq_users_google_id", ["google_id"])


def downgrade():
    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_users_google_id", type_="unique")
        batch_op.drop_constraint("uq_users_username", type_="unique")
        batch_op.drop_column("oauth_provider")
        batch_op.drop_column("google_id")
        batch_op.drop_column("profile_picture_url")
        batch_op.drop_column("bio")
        batch_op.drop_column("full_name")
        batch_op.drop_column("username")
