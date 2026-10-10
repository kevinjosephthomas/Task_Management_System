"""Database operations."""
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password
from app.transitions import validate_transition


# ── User operations ───────────────────────────────────────────────────────────

def create_user(db: Session, email: str, password: str) -> models.User:
    """Create a new user. Raise ValueError if email already exists."""
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise ValueError(f"Email {email} already registered")
    user = models.User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Return user if email and password match, else None."""
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ── Task operations ───────────────────────────────────────────────────────────

def _compute_overdue(task: models.Task) -> models.Task:
    task.is_overdue = bool(
        task.due_date and task.due_date < date.today() and task.status != "completed"
    )
    return task


def create_task(db: Session, user_id: int, data: schemas.TaskCreate) -> models.Task:
    task = models.Task(
        title=data.title,
        description=data.description,
        status="pending",
        priority=data.priority.value if data.priority else "medium",
        due_date=data.due_date,
        user_id=user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _compute_overdue(task)


def list_tasks(
    db: Session,
    user_id: int,
    filters: Optional[schemas.TaskFilter] = None,
) -> List[models.Task]:
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    if filters:
        if filters.status:
            query = query.filter(models.Task.status == filters.status)
        if filters.priority:
            query = query.filter(models.Task.priority == filters.priority)

        if filters.sort_by == "due_date":
            query = query.order_by(models.Task.due_date.asc().nullslast())
        elif filters.sort_by == "priority":
            query = query.order_by(models.Task.priority)
        else:
            query = query.order_by(models.Task.created_at.desc())
    else:
        query = query.order_by(models.Task.created_at.desc())

    return [_compute_overdue(t) for t in query.all()]


def get_task(db: Session, task_id: int, user_id: int) -> Optional[models.Task]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    return _compute_overdue(task) if task else None


def update_task(db: Session, task: models.Task, data: schemas.TaskUpdate) -> models.Task:
    changes = data.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise ValueError("title cannot be null")
    if "status" in changes:
        if changes["status"] is None:
            raise ValueError("status cannot be null")
        validate_transition(task.status, changes["status"].value)  # may raise InvalidTransition
        changes["status"] = changes["status"].value
    if "priority" in changes and changes["priority"] is not None:
        changes["priority"] = changes["priority"].value
    for key, value in changes.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return _compute_overdue(task)


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
