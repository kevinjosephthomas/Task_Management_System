"""Database operations."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.transitions import validate_transition


def create_task(db: Session, data: schemas.TaskCreate) -> models.Task:
    task = models.Task(title=data.title, description=data.description, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session) -> List[models.Task]:
    return db.query(models.Task).order_by(models.Task.id).all()


def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.get(models.Task, task_id)


def update_task(db: Session, task: models.Task, data: schemas.TaskUpdate) -> models.Task:
    changes = data.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise ValueError("title cannot be null")
    if "status" in changes:
        if changes["status"] is None:
            raise ValueError("status cannot be null")
        validate_transition(task.status, changes["status"].value)  # may raise InvalidTransition
        changes["status"] = changes["status"].value
    for key, value in changes.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
