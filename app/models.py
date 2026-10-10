"""SQLAlchemy ORM models (mirrors the schema created by Alembic)."""
from sqlalchemy import CheckConstraint, Column, Integer, Text, TIMESTAMP, text

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("status IN ('pending','in-progress','completed')", name="ck_tasks_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="pending", server_default="pending")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
