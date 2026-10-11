"""add task_collaborators, task_notifications, assigned_to/by on tasks

Revision ID: 0008
Revises: 0007
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires batch mode to add FK columns
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("assigned_to_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("assigned_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_tasks_assigned_to", "users", ["assigned_to_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_tasks_assigned_by", "users", ["assigned_by_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "task_collaborators",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False, server_default=sa.text("'viewer'")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("task_id", "user_id", name="uq_task_collaborator"),
    )

    op.create_table(
        "task_notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    op.drop_table("task_notifications")
    op.drop_table("task_collaborators")
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_tasks_assigned_by", type_="foreignkey")
        batch_op.drop_constraint("fk_tasks_assigned_to", type_="foreignkey")
        batch_op.drop_column("assigned_by_id")
        batch_op.drop_column("assigned_to_id")
