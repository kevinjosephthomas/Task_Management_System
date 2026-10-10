"""SQLAlchemy ORM models (mirrors the schema created by Alembic)."""
from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, String, Text, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("status IN ('pending','in-progress','completed')", name="ck_tasks_status"),
        CheckConstraint("priority IN ('low','medium','high')", name="ck_tasks_priority"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="pending", server_default="pending")
    priority = Column(Text, nullable=False, default="medium", server_default="medium")
    due_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    owner = relationship("User", back_populates="tasks")
