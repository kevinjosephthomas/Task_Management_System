"""add user_id to tasks table

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires batch mode to add a column with a FK
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tasks_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )


def downgrade():
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_tasks_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
