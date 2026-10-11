"""FastAPI application: routes, error handling, CORS."""
import csv
import io
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import create_access_token
from app.database import get_current_user, get_db
from app.transitions import InvalidTransition

app = FastAPI(
    title="Task Management API",
    description="CRUD API for tasks with authentication, Kanban board, priorities, due dates, and analytics.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Task Management API v2. See /docs for Swagger UI."}


# -- Auth endpoints (public) --------------------------------------------------

@app.post(
    "/auth/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    operation_id="register_user",
)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user.email, user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/auth/login",
    response_model=schemas.TokenResponse,
    tags=["auth"],
    operation_id="login_user",
)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, expire = create_access_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": int((expire - datetime.now(timezone.utc)).total_seconds()),
    }


# -- Task endpoints (protected) -----------------------------------------------

@app.post(
    "/tasks/",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
    operation_id="create_task",
)
def create_task(
    task: schemas.TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.create_task(db, current_user["id"], task)


@app.get(
    "/tasks/",
    response_model=List[schemas.TaskOut],
    tags=["tasks"],
    operation_id="list_tasks",
)
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    sort_by: Optional[str] = Query("created_at"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = schemas.TaskFilter(
        status=status_filter,
        priority=priority_filter,
        sort_by=sort_by,
    )
    return crud.list_tasks(db, current_user["id"], filters)


@app.get(
    "/tasks/stats/summary",
    tags=["analytics"],
    operation_id="get_task_stats",
)
def get_task_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return task statistics for the current user."""
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user["id"]).all()
    today = date.today()

    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in-progress")
    completed = sum(1 for t in tasks if t.status == "completed")
    overdue = sum(
        1 for t in tasks
        if t.due_date and t.due_date < today and t.status != "completed"
    )
    completion_pct = (completed / total * 100) if total > 0 else 0

    by_priority = {
        "high": sum(1 for t in tasks if t.priority == "high"),
        "medium": sum(1 for t in tasks if t.priority == "medium"),
        "low": sum(1 for t in tasks if t.priority == "low"),
    }

    return {
        "total_tasks": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "completion_percentage": round(completion_pct, 1),
        "by_priority": by_priority,
    }


# -- Feature 5: Search & Filter -----------------------------------------------

@app.post(
    "/tasks/search",
    response_model=schemas.TaskListResponse,
    tags=["tasks"],
    operation_id="search_tasks",
)
def search_tasks(
    filter_req: schemas.TaskFilterRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = min(limit, 500)
    total, tasks = crud.search_and_filter_tasks(
        db,
        user_id=current_user["id"],
        search=filter_req.search,
        status=filter_req.status,
        priority=filter_req.priority,
        sort_by=filter_req.sort_by,
        sort_order=filter_req.sort_order,
        due_date_from=filter_req.due_date_from,
        due_date_to=filter_req.due_date_to,
        limit=limit,
        offset=skip,
    )
    return {"total": total, "count": len(tasks), "tasks": tasks}


# -- Feature 6: Reminders -----------------------------------------------------

@app.get(
    "/tasks/reminders/overdue",
    tags=["reminders"],
    operation_id="get_overdue_tasks",
)
def get_overdue_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = crud.get_overdue_tasks(db, current_user["id"])
    return {"count": len(tasks), "tasks": tasks}


@app.get(
    "/tasks/reminders/upcoming",
    tags=["reminders"],
    operation_id="get_upcoming_tasks",
)
def get_upcoming_tasks(
    days_ahead: int = Query(3, ge=1),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = crud.get_upcoming_tasks(db, current_user["id"], days_ahead)
    return {"count": len(tasks), "tasks": tasks}


# -- Feature 10: Export CSV ----------------------------------------------------

@app.post(
    "/tasks/export/csv",
    tags=["tasks"],
    operation_id="export_tasks_csv",
)
def export_tasks_csv(
    filter_req: schemas.TaskFilterRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, tasks = crud.search_and_filter_tasks(
        db,
        user_id=current_user["id"],
        search=filter_req.search,
        status=filter_req.status,
        priority=filter_req.priority,
        sort_by=filter_req.sort_by,
        sort_order=filter_req.sort_order,
        due_date_from=filter_req.due_date_from,
        due_date_to=filter_req.due_date_to,
        limit=500,
        offset=0,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "description", "status", "priority", "due_date", "created_at"])
    for t in tasks:
        writer.writerow([t.id, t.title, t.description, t.status, t.priority, t.due_date, t.created_at])

    output.seek(0)
    filename = f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# -- Feature 7: Activity endpoints ---------------------------------------------

@app.get(
    "/tasks/user/activity-summary",
    tags=["activity"],
    operation_id="get_user_activity_summary",
)
def get_user_activity_summary(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activities = crud.get_user_activity_summary(db, current_user["id"], limit)
    return {"count": len(activities), "activities": activities}


# -- Feature 9: Collaboration -------------------------------------------------

@app.get(
    "/tasks/shared",
    response_model=List[schemas.TaskOut],
    tags=["collaboration"],
    operation_id="get_shared_tasks",
)
def get_shared_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_shared_tasks_for_user(db, current_user["id"])


# -- Single task endpoints (must be after /tasks/... paths) --------------------

@app.get(
    "/tasks/{task_id}",
    response_model=schemas.TaskOut,
    tags=["tasks"],
    operation_id="get_task",
)
def get_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user["id"])
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=schemas.TaskOut,
    tags=["tasks"],
    operation_id="update_task",
)
def update_task(
    task_id: int,
    update: schemas.TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user["id"])
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    try:
        return crud.update_task(db, task, update, current_user["id"])
    except InvalidTransition as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["tasks"],
    operation_id="delete_task",
)
def delete_task(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user["id"])
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    crud.delete_task(db, task, current_user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Feature 7: Task Activity -------------------------------------------------

@app.get(
    "/tasks/{task_id}/activity",
    tags=["activity"],
    operation_id="get_task_activity",
)
def get_task_activity(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activities = crud.get_task_activity(db, task_id, current_user["id"])
    if activities is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"task_id": task_id, "count": len(activities), "activities": activities}


# -- Feature 8: Subtask endpoints ----------------------------------------------

@app.post(
    "/tasks/{task_id}/subtasks",
    response_model=schemas.SubtaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["subtasks"],
    operation_id="create_subtask",
)
def create_subtask(
    task_id: int,
    data: schemas.SubtaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subtask = crud.create_subtask(db, task_id, current_user["id"], data)
    if not subtask:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return subtask


@app.get(
    "/tasks/{task_id}/subtasks",
    response_model=List[schemas.SubtaskOut],
    tags=["subtasks"],
    operation_id="list_subtasks",
)
def list_subtasks(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = crud.get_subtasks(db, task_id, current_user["id"])
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return result


@app.get(
    "/tasks/{task_id}/subtasks/completion",
    tags=["subtasks"],
    operation_id="get_subtask_completion",
)
def get_subtask_completion(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user["id"])
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return crud.get_subtask_completion(db, task_id)


@app.put(
    "/tasks/{task_id}/subtasks/{subtask_id}",
    response_model=schemas.SubtaskOut,
    tags=["subtasks"],
    operation_id="update_subtask",
)
def update_subtask(
    task_id: int,
    subtask_id: int,
    data: schemas.SubtaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subtask = crud.get_subtask(db, subtask_id, current_user["id"])
    if not subtask or subtask.task_id != task_id:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return crud.update_subtask(db, subtask, current_user["id"], data)


@app.delete(
    "/tasks/{task_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["subtasks"],
    operation_id="delete_subtask",
)
def delete_subtask(
    task_id: int,
    subtask_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subtask = crud.get_subtask(db, subtask_id, current_user["id"])
    if not subtask or subtask.task_id != task_id:
        raise HTTPException(status_code=404, detail="Subtask not found")
    crud.delete_subtask(db, subtask, current_user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Feature 9: Collaboration endpoints ----------------------------------------

@app.post(
    "/tasks/{task_id}/share",
    tags=["collaboration"],
    operation_id="share_task",
)
def share_task(
    task_id: int,
    data: schemas.ShareTaskRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        shared = crud.share_task(db, task_id, current_user["id"], data.email, data.permission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not shared:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or not owned by you")
    return {"id": shared.id, "message": f"Task shared with {data.email}"}


@app.post(
    "/tasks/{task_id}/comments",
    tags=["collaboration"],
    operation_id="add_comment",
)
def add_comment(
    task_id: int,
    data: schemas.CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = crud.add_comment(db, task_id, current_user["id"], data.content)
    if not comment:
        raise HTTPException(status_code=403, detail="No access to this task")
    return {"id": comment.id, "message": "Comment added"}


@app.get(
    "/tasks/{task_id}/comments",
    tags=["collaboration"],
    operation_id="get_comments",
)
def get_comments(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comments = crud.get_comments(db, task_id, current_user["id"])
    if comments is None:
        raise HTTPException(status_code=403, detail="No access to this task")
    return {"task_id": task_id, "count": len(comments), "comments": comments}
