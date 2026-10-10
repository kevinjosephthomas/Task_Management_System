"""Pydantic request/response schemas."""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in-progress"
    completed = "completed"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


def _clean_title(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("title must not be blank")
    return v


# ── Auth schemas ──────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: Optional[datetime] = None


# ── Task schemas ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """New tasks always start as 'pending', so status is not accepted here."""
    title: str = Field(..., max_length=200, examples=["Write report"])
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Priority] = Priority.medium
    due_date: Optional[date] = None

    _v_title = field_validator("title")(_clean_title)


class TaskUpdate(BaseModel):
    """All fields optional (partial update)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None

    _v_title = field_validator("title")(_clean_title)


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: Priority = Priority.medium
    due_date: Optional[date] = None
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None
    is_overdue: Optional[bool] = None


class TaskFilter(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    sort_by: Optional[str] = "created_at"  # "created_at", "due_date", "priority"


class ErrorResponse(BaseModel):
    detail: str
