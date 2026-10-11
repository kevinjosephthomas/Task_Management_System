"""SQLAlchemy ORM models (mirrors the schema created by Alembic)."""
from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, ForeignKey, Integer,
    String, Text, TIMESTAMP, UniqueConstraint, text,
)
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
    activities = relationship("TaskActivity", back_populates="task", cascade="all, delete-orphan")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    shared_entries = relationship("SharedTask", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class TaskActivity(Base):
    __tablename__ = "task_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)
    field_name = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="activities")
    user = relationship("User", foreign_keys=[user_id])


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    position = Column(Integer, default=0, server_default=text("0"))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="subtasks")


class SharedTask(Base):
    __tablename__ = "shared_tasks"
    __table_args__ = (
        UniqueConstraint("task_id", "owner_id", "shared_with_id", name="uq_shared_task"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String(20), nullable=False, default="view", server_default=text("'view'"))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="shared_entries")
    owner = relationship("User", foreign_keys=[owner_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])
