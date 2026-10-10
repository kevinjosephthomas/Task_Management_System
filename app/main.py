"""FastAPI application: routes, error handling, CORS."""
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.transitions import InvalidTransition

app = FastAPI(
    title="Task Management API",
    description="CRUD API for tasks with strict status transitions: "
                "pending -> in-progress -> completed.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NOT_FOUND = {404: {"model": schemas.ErrorResponse, "description": "Task not found"}}


def _get_or_404(db: Session, task_id: int):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Task Management API. See /docs for Swagger UI."}


@app.post("/tasks/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED,
          tags=["tasks"], operation_id="create_task")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)


@app.get("/tasks/", response_model=List[schemas.TaskOut], tags=["tasks"],
         operation_id="list_tasks")
def list_tasks(db: Session = Depends(get_db)):
    return crud.list_tasks(db)


@app.get("/tasks/{task_id}", response_model=schemas.TaskOut, responses=NOT_FOUND,
         tags=["tasks"], operation_id="get_task")
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, task_id)


@app.put("/tasks/{task_id}", response_model=schemas.TaskOut,
         responses={**NOT_FOUND,
                    400: {"model": schemas.ErrorResponse, "description": "Invalid status transition"}},
         tags=["tasks"], operation_id="update_task")
def update_task(task_id: int, update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    try:
        return crud.update_task(db, task, update)
    except InvalidTransition as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT,
            responses=NOT_FOUND, tags=["tasks"], operation_id="delete_task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    crud.delete_task(db, _get_or_404(db, task_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
