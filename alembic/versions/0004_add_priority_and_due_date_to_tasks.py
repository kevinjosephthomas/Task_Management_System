"""add priority and due_date to tasks

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("priority", sa.String(10), nullable=False, server_default="medium"))
    op.add_column("tasks", sa.Column("due_date", sa.Date(), nullable=True))
    # SQLite batch mode required for check constraints
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.create_check_constraint(
            "ck_tasks_priority",
            "priority IN ('low','medium','high')"
        )


def downgrade():
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("ck_tasks_priority", type_="check")
        batch_op.drop_column("due_date")
        batch_op.drop_column("priority")
