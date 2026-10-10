"""FastAPI application: routes, error handling, CORS."""
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
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


# ── Auth endpoints (public) ───────────────────────────────────────────────────

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


# ── Task endpoints (protected) ────────────────────────────────────────────────

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
        return crud.update_task(db, task, update)
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
    crud.delete_task(db, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
