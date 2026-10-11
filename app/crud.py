"""Database operations."""
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password
from app.transitions import validate_transition


# -- User operations -----------------------------------------------------------

def create_user(db: Session, email: str, password: str, username: str = None, full_name: str = None) -> models.User:
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise ValueError(f"Email {email} already registered")
    if username:
        existing_username = db.query(models.User).filter(models.User.username == username).first()
        if existing_username:
            raise ValueError(f"Username {username} already taken")
    user = models.User(
        email=email,
        hashed_password=hash_password(password),
        username=username,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.google_id == google_id).first()


def create_or_get_google_user(db: Session, google_id: str, email: str, full_name: str = None, picture: str = None) -> models.User:
    user = get_user_by_google_id(db, google_id)
    if user:
        return user
    user = get_user_by_email(db, email)
    if user:
        user.google_id = google_id
        user.oauth_provider = "google"
        if full_name and not user.full_name:
            user.full_name = full_name
        if picture and not user.profile_picture_url:
            user.profile_picture_url = picture
        db.commit()
        db.refresh(user)
        return user
    user = models.User(
        email=email,
        google_id=google_id,
        oauth_provider="google",
        full_name=full_name,
        profile_picture_url=picture,
        hashed_password=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_profile(db: Session, user_id: int, data: schemas.UserProfileUpdate) -> Optional[models.User]:
    user = db.get(models.User, user_id)
    if not user:
        return None
    changes = data.model_dump(exclude_unset=True)
    if "username" in changes and changes["username"]:
        existing = db.query(models.User).filter(
            models.User.username == changes["username"],
            models.User.id != user_id,
        ).first()
        if existing:
            raise ValueError(f"Username {changes['username']} already taken")
    for key, value in changes.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


# -- Task operations -----------------------------------------------------------

def _compute_overdue(task: models.Task) -> models.Task:
    task.is_overdue = bool(
        task.due_date and task.due_date < date.today() and task.status != "completed"
    )
    if not task.is_overdue and task.due_datetime:
        task.is_overdue = bool(
            task.due_datetime.replace(tzinfo=None) < datetime.utcnow()
            and task.status != "completed"
        )
    return task


def _compute_subtask_completion(db: Session, task: models.Task) -> models.Task:
    total = db.query(func.count(models.Subtask.id)).filter(
        models.Subtask.task_id == task.id
    ).scalar() or 0
    completed = db.query(func.count(models.Subtask.id)).filter(
        models.Subtask.task_id == task.id,
        models.Subtask.completed == True,
    ).scalar() or 0
    percentage = round((completed / total * 100), 1) if total > 0 else 0.0
    task.subtask_completion = {"total": total, "completed": completed, "percentage": percentage}
    return task


def _compute_deadline_info(db: Session, task: models.Task) -> models.Task:
    now = datetime.utcnow()
    deadline_dt = None
    if task.due_datetime:
        deadline_dt = task.due_datetime.replace(tzinfo=None) if task.due_datetime.tzinfo else task.due_datetime
    elif task.due_date:
        deadline_dt = datetime.combine(task.due_date, datetime.max.time())

    if deadline_dt and task.status != "completed":
        diff = deadline_dt - now
        total_seconds = int(diff.total_seconds())
        is_past = total_seconds < 0
        abs_seconds = abs(total_seconds)
        days = abs_seconds // 86400
        hours = (abs_seconds % 86400) // 3600
        minutes = (abs_seconds % 3600) // 60

        task.deadline_info = {
            "deadline": deadline_dt.isoformat(),
            "is_past_due": is_past,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "total_seconds": total_seconds,
            "human_readable": f"{'Overdue by' if is_past else 'Due in'} {days}d {hours}h {minutes}m",
        }
    else:
        task.deadline_info = None
    return task


def _compute_assigned_email(db: Session, task: models.Task) -> models.Task:
    if task.assigned_to_id:
        assigned_user = db.get(models.User, task.assigned_to_id)
        task.assigned_to_email = assigned_user.email if assigned_user else None
    else:
        task.assigned_to_email = None
    return task


def _enrich_task(db: Session, task: models.Task) -> models.Task:
    _compute_overdue(task)
    _compute_subtask_completion(db, task)
    _compute_deadline_info(db, task)
    _compute_assigned_email(db, task)
    return task


def create_task(db: Session, user_id: int, data: schemas.TaskCreate) -> models.Task:
    assigned_to_id = None
    if data.assigned_to_email:
        target = get_user_by_email(db, data.assigned_to_email)
        if not target:
            raise ValueError(f"User {data.assigned_to_email} not found")
        assigned_to_id = target.id

    task = models.Task(
        title=data.title,
        description=data.description,
        status="pending",
        priority=data.priority.value if data.priority else "medium",
        due_date=data.due_date,
        due_datetime=data.due_datetime,
        user_id=user_id,
        assigned_to_id=assigned_to_id,
        assigned_by_id=user_id if assigned_to_id else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    log_activity(db, task.id, user_id, "created", new_value=task.title)

    if assigned_to_id and assigned_to_id != user_id:
        assigner = db.get(models.User, user_id)
        create_notification(
            db, assigned_to_id, task.id, "task_assigned",
            f"You were assigned to '{task.title}' by {assigner.email if assigner else 'someone'}",
        )

    return _enrich_task(db, task)


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

    return [_enrich_task(db, t) for t in query.all()]


def get_task(db: Session, task_id: int, user_id: int) -> Optional[models.Task]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    return _enrich_task(db, task) if task else None


def update_task(db: Session, task: models.Task, data: schemas.TaskUpdate, user_id: int = None) -> models.Task:
    changes = data.model_dump(exclude_unset=True)

    assigned_to_email = changes.pop("assigned_to_email", None)

    if "title" in changes and changes["title"] is None:
        raise ValueError("title cannot be null")
    if "status" in changes:
        if changes["status"] is None:
            raise ValueError("status cannot be null")
        validate_transition(task.status, changes["status"].value)
        changes["status"] = changes["status"].value

    if "priority" in changes and changes["priority"] is not None:
        changes["priority"] = changes["priority"].value

    uid = user_id or task.user_id
    for key, value in changes.items():
        old_val = str(getattr(task, key)) if getattr(task, key) is not None else None
        new_val = str(value) if value is not None else None
        action = "status_changed" if key == "status" else "updated"
        if old_val != new_val:
            log_activity(db, task.id, uid, action, field_name=key, old_value=old_val, new_value=new_val)
        setattr(task, key, value)

    if assigned_to_email is not None:
        target = get_user_by_email(db, assigned_to_email)
        if not target:
            raise ValueError(f"User {assigned_to_email} not found")
        old_assigned = task.assigned_to_id
        task.assigned_to_id = target.id
        task.assigned_by_id = uid
        if target.id != old_assigned and target.id != uid:
            assigner = db.get(models.User, uid)
            create_notification(
                db, target.id, task.id, "task_assigned",
                f"You were assigned to '{task.title}' by {assigner.email if assigner else 'someone'}",
            )

    db.commit()
    db.refresh(task)
    return _enrich_task(db, task)


def delete_task(db: Session, task: models.Task, user_id: int = None) -> None:
    db.delete(task)
    db.commit()


# -- Feature 5: Search & Filter -----------------------------------------------

PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}


def search_and_filter_tasks(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[int, List[models.Task]]:
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Task.title).like(pattern),
                func.lower(models.Task.description).like(pattern),
            )
        )

    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if due_date_from:
        query = query.filter(models.Task.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(models.Task.due_date <= due_date_to)

    total = query.count()

    is_desc = sort_order == "desc"
    if sort_by == "due_date":
        col = models.Task.due_date.desc() if is_desc else models.Task.due_date.asc()
        query = query.order_by(col.nullslast())
    elif sort_by == "priority":
        col = models.Task.priority.desc() if is_desc else models.Task.priority.asc()
        query = query.order_by(col)
    elif sort_by == "status":
        col = models.Task.status.desc() if is_desc else models.Task.status.asc()
        query = query.order_by(col)
    elif sort_by == "title":
        col = models.Task.title.desc() if is_desc else models.Task.title.asc()
        query = query.order_by(col)
    else:
        col = models.Task.created_at.desc() if is_desc else models.Task.created_at.asc()
        query = query.order_by(col)

    limit = min(limit, 500)
    tasks = query.offset(offset).limit(limit).all()
    return total, [_enrich_task(db, t) for t in tasks]


# -- Feature 6: Reminders -----------------------------------------------------

def get_overdue_tasks(db: Session, user_id: int) -> List[dict]:
    today = date.today()
    tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.due_date < today,
        models.Task.status != "completed",
    ).order_by(models.Task.due_date.asc()).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "status": t.status,
            "priority": t.priority,
            "days_overdue": (today - t.due_date).days,
        }
        for t in tasks
    ]


def get_upcoming_tasks(db: Session, user_id: int, days_ahead: int = 3) -> List[dict]:
    today = date.today()
    end = today + timedelta(days=days_ahead)
    tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.due_date >= today,
        models.Task.due_date <= end,
        models.Task.status != "completed",
    ).order_by(models.Task.due_date.asc()).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "status": t.status,
            "priority": t.priority,
            "days_until_due": (t.due_date - today).days,
        }
        for t in tasks
    ]


# -- Feature 7: Activity logging -----------------------------------------------

def log_activity(
    db: Session,
    task_id: int,
    user_id: int,
    action: str,
    field_name: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> models.TaskActivity:
    activity = models.TaskActivity(
        task_id=task_id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_task_activity(db: Session, task_id: int, user_id: int) -> Optional[List[dict]]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    if not task:
        return None

    activities = db.query(models.TaskActivity).filter(
        models.TaskActivity.task_id == task_id,
    ).order_by(models.TaskActivity.created_at.desc()).all()

    result = []
    for a in activities:
        user = db.get(models.User, a.user_id)
        result.append({
            "id": a.id,
            "action": a.action,
            "field_name": a.field_name,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "user_email": user.email if user else None,
            "created_at": str(a.created_at) if a.created_at else None,
        })
    return result


def get_user_activity_summary(db: Session, user_id: int, limit: int = 20) -> List[dict]:
    activities = (
        db.query(models.TaskActivity)
        .join(models.Task, models.TaskActivity.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .order_by(models.TaskActivity.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for a in activities:
        task = db.get(models.Task, a.task_id)
        result.append({
            "id": a.id,
            "task_id": a.task_id,
            "task_title": task.title if task else None,
            "action": a.action,
            "field_name": a.field_name,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "created_at": str(a.created_at) if a.created_at else None,
        })
    return result


# -- Feature 8: Subtasks ------------------------------------------------------

def create_subtask(db: Session, task_id: int, user_id: int, data: schemas.SubtaskCreate) -> Optional[models.Subtask]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    if not task:
        return None

    max_pos = db.query(func.max(models.Subtask.position)).filter(
        models.Subtask.task_id == task_id,
    ).scalar() or 0

    subtask = models.Subtask(
        task_id=task_id,
        title=data.title,
        description=data.description,
        position=max_pos + 1,
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    log_activity(db, task_id, user_id, "updated", field_name="subtask", new_value=f"Added: {data.title}")
    return subtask


def get_subtasks(db: Session, task_id: int, user_id: int) -> Optional[List[models.Subtask]]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    if not task:
        return None
    return db.query(models.Subtask).filter(
        models.Subtask.task_id == task_id,
    ).order_by(models.Subtask.position.asc()).all()


def get_subtask(db: Session, subtask_id: int, user_id: int) -> Optional[models.Subtask]:
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        return None
    task = db.query(models.Task).filter(
        models.Task.id == subtask.task_id,
        models.Task.user_id == user_id,
    ).first()
    if not task:
        return None
    return subtask


def update_subtask(db: Session, subtask: models.Subtask, user_id: int, data: schemas.SubtaskUpdate) -> models.Subtask:
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(subtask, key, value)
    db.commit()
    db.refresh(subtask)
    log_activity(db, subtask.task_id, user_id, "updated", field_name="subtask", new_value=f"Updated: {subtask.title}")
    return subtask


def delete_subtask(db: Session, subtask: models.Subtask, user_id: int) -> None:
    log_activity(db, subtask.task_id, user_id, "updated", field_name="subtask", new_value=f"Deleted: {subtask.title}")
    db.delete(subtask)
    db.commit()


def get_subtask_completion(db: Session, task_id: int) -> dict:
    total = db.query(func.count(models.Subtask.id)).filter(
        models.Subtask.task_id == task_id,
    ).scalar() or 0
    completed = db.query(func.count(models.Subtask.id)).filter(
        models.Subtask.task_id == task_id,
        models.Subtask.completed == True,
    ).scalar() or 0
    percentage = round((completed / total * 100), 1) if total > 0 else 0.0
    return {"total": total, "completed": completed, "percentage": percentage}


# -- Feature 9: Collaboration -------------------------------------------------

def share_task(db: Session, task_id: int, owner_id: int, shared_with_email: str, permission: str = "view") -> Optional[models.SharedTask]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == owner_id,
    ).first()
    if not task:
        return None

    target_user = get_user_by_email(db, shared_with_email)
    if not target_user:
        raise ValueError(f"User {shared_with_email} not found")
    if target_user.id == owner_id:
        raise ValueError("Cannot share task with yourself")

    existing = db.query(models.SharedTask).filter(
        models.SharedTask.task_id == task_id,
        models.SharedTask.owner_id == owner_id,
        models.SharedTask.shared_with_id == target_user.id,
    ).first()
    if existing:
        raise ValueError("Task already shared with this user")

    shared = models.SharedTask(
        task_id=task_id,
        owner_id=owner_id,
        shared_with_id=target_user.id,
        permission=permission,
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)
    return shared


def is_collaborator(db: Session, task_id: int, user_id: int) -> bool:
    return db.query(models.SharedTask).filter(
        models.SharedTask.task_id == task_id,
        models.SharedTask.shared_with_id == user_id,
    ).first() is not None


def can_access_task(db: Session, task_id: int, user_id: int) -> bool:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return False
    if task.user_id == user_id:
        return True
    if task.assigned_to_id == user_id:
        return True
    if is_collaborator(db, task_id, user_id):
        return True
    collab = db.query(models.TaskCollaborator).filter(
        models.TaskCollaborator.task_id == task_id,
        models.TaskCollaborator.user_id == user_id,
    ).first()
    return collab is not None


def add_comment(db: Session, task_id: int, user_id: int, content: str) -> Optional[models.TaskComment]:
    if not can_access_task(db, task_id, user_id):
        return None

    comment = models.TaskComment(
        task_id=task_id,
        user_id=user_id,
        content=content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, task_id: int, user_id: int) -> Optional[List[dict]]:
    if not can_access_task(db, task_id, user_id):
        return None

    comments = db.query(models.TaskComment).filter(
        models.TaskComment.task_id == task_id,
    ).order_by(models.TaskComment.created_at.desc()).all()

    result = []
    for c in comments:
        user = db.get(models.User, c.user_id)
        result.append({
            "id": c.id,
            "task_id": c.task_id,
            "user_email": user.email if user else None,
            "content": c.content,
            "created_at": str(c.created_at) if c.created_at else None,
            "updated_at": str(c.updated_at) if c.updated_at else None,
        })
    return result


def get_shared_tasks_for_user(db: Session, user_id: int) -> List[models.Task]:
    shared = db.query(models.SharedTask).filter(
        models.SharedTask.shared_with_id == user_id,
    ).all()
    tasks = []
    for s in shared:
        task = db.get(models.Task, s.task_id)
        if task:
            _enrich_task(db, task)
            tasks.append(task)
    return tasks


# -- Feature A: Enhanced Collaboration ----------------------------------------

def assign_task(db: Session, task_id: int, owner_id: int, assignee_email: str) -> Optional[models.Task]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == owner_id,
    ).first()
    if not task:
        return None

    target = get_user_by_email(db, assignee_email)
    if not target:
        raise ValueError(f"User {assignee_email} not found")

    old_assigned = task.assigned_to_id
    task.assigned_to_id = target.id
    task.assigned_by_id = owner_id
    db.commit()
    db.refresh(task)

    log_activity(db, task.id, owner_id, "updated", field_name="assigned_to", new_value=assignee_email)

    if target.id != owner_id and target.id != old_assigned:
        assigner = db.get(models.User, owner_id)
        create_notification(
            db, target.id, task.id, "task_assigned",
            f"You were assigned to '{task.title}' by {assigner.email if assigner else 'someone'}",
        )

    return _enrich_task(db, task)


def add_collaborator(db: Session, task_id: int, owner_id: int, collab_email: str, role: str = "viewer") -> Optional[models.TaskCollaborator]:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == owner_id,
    ).first()
    if not task:
        return None

    target = get_user_by_email(db, collab_email)
    if not target:
        raise ValueError(f"User {collab_email} not found")
    if target.id == owner_id:
        raise ValueError("Cannot add yourself as a collaborator")

    existing = db.query(models.TaskCollaborator).filter(
        models.TaskCollaborator.task_id == task_id,
        models.TaskCollaborator.user_id == target.id,
    ).first()
    if existing:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    collab = models.TaskCollaborator(
        task_id=task_id,
        user_id=target.id,
        role=role,
    )
    db.add(collab)
    db.commit()
    db.refresh(collab)

    owner = db.get(models.User, owner_id)
    create_notification(
        db, target.id, task_id, "collaborator_added",
        f"You were added as {role} on '{task.title}' by {owner.email if owner else 'someone'}",
    )
    return collab


def get_collaborators(db: Session, task_id: int, user_id: int) -> Optional[List[dict]]:
    if not can_access_task(db, task_id, user_id):
        return None
    collabs = db.query(models.TaskCollaborator).filter(
        models.TaskCollaborator.task_id == task_id,
    ).all()
    result = []
    for c in collabs:
        user = db.get(models.User, c.user_id)
        result.append({
            "id": c.id,
            "task_id": c.task_id,
            "user_id": c.user_id,
            "user_email": user.email if user else None,
            "role": c.role,
            "created_at": str(c.created_at) if c.created_at else None,
        })
    return result


def remove_collaborator(db: Session, task_id: int, owner_id: int, collaborator_id: int) -> bool:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == owner_id,
    ).first()
    if not task:
        return False
    collab = db.query(models.TaskCollaborator).filter(
        models.TaskCollaborator.id == collaborator_id,
        models.TaskCollaborator.task_id == task_id,
    ).first()
    if not collab:
        return False
    db.delete(collab)
    db.commit()
    return True


# -- Notifications ------------------------------------------------------------

def create_notification(db: Session, user_id: int, task_id: Optional[int], ntype: str, message: str) -> models.TaskNotification:
    notif = models.TaskNotification(
        user_id=user_id,
        task_id=task_id,
        type=ntype,
        message=message,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications(db: Session, user_id: int, unread_only: bool = False, limit: int = 50) -> List[models.TaskNotification]:
    query = db.query(models.TaskNotification).filter(
        models.TaskNotification.user_id == user_id,
    )
    if unread_only:
        query = query.filter(models.TaskNotification.read == False)
    return query.order_by(models.TaskNotification.created_at.desc()).limit(limit).all()


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    notif = db.query(models.TaskNotification).filter(
        models.TaskNotification.id == notification_id,
        models.TaskNotification.user_id == user_id,
    ).first()
    if not notif:
        return False
    notif.read = True
    db.commit()
    return True


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    count = db.query(models.TaskNotification).filter(
        models.TaskNotification.user_id == user_id,
        models.TaskNotification.read == False,
    ).update({"read": True})
    db.commit()
    return count


def get_tasks_assigned_to_user(db: Session, user_id: int) -> List[models.Task]:
    tasks = db.query(models.Task).filter(
        models.Task.assigned_to_id == user_id,
    ).order_by(models.Task.created_at.desc()).all()
    return [_enrich_task(db, t) for t in tasks]


def get_tasks_with_deadline_soon(db: Session, hours_ahead: int = 24) -> List[models.Task]:
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours_ahead)
    tasks = db.query(models.Task).filter(
        models.Task.due_datetime != None,
        models.Task.due_datetime <= cutoff,
        models.Task.due_datetime > now,
        models.Task.status != "completed",
    ).all()
    return tasks
