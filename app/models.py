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
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    username = Column(String(100), nullable=True, unique=True)
    full_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    google_id = Column(String(255), nullable=True, unique=True)
    oauth_provider = Column(String(50), nullable=True)
    timezone = Column(String(50), nullable=True, server_default=text("'UTC'"))

    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.user_id", cascade="all, delete-orphan")


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
    due_datetime = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    owner = relationship("User", back_populates="tasks", foreign_keys=[user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    activities = relationship("TaskActivity", back_populates="task", cascade="all, delete-orphan")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    shared_entries = relationship("SharedTask", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    collaborators = relationship("TaskCollaborator", back_populates="task", cascade="all, delete-orphan")
    notifications = relationship("TaskNotification", back_populates="task", cascade="all, delete-orphan")


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


class TaskCollaborator(Base):
    __tablename__ = "task_collaborators"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_collaborator"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer", server_default=text("'viewer'"))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])


class TaskNotification(Base):
    __tablename__ = "task_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task", back_populates="notifications")
