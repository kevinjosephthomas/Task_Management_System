"""Pydantic request/response schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in-progress"
    completed = "completed"


def _clean_title(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("title must not be blank")
    return v


class TaskCreate(BaseModel):
    """New tasks always start as 'pending', so status is not accepted here."""
    title: str = Field(..., max_length=200, examples=["Write report"])
    description: Optional[str] = Field(None, max_length=2000)

    _v_title = field_validator("title")(_clean_title)


class TaskUpdate(BaseModel):
    """All fields optional (partial update)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None

    _v_title = field_validator("title")(_clean_title)


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    created_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    detail: str
