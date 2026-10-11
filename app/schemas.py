"""Pydantic request/response schemas."""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in-progress"
    completed = "completed"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CollaboratorRole(str, Enum):
    owner = "owner"
    manager = "manager"
    contributor = "contributor"
    viewer = "viewer"


def _clean_title(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("title must not be blank")
    return v


# -- Auth schemas -------------------------------------------------------------

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()


class UserLogin(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    oauth_provider: Optional[str] = None
    timezone: Optional[str] = "UTC"
    created_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    profile_picture_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)


# -- Task schemas --------------------------------------------------------------

class TaskCreate(BaseModel):
    """New tasks always start as 'pending', so status is not accepted here."""
    title: str = Field(..., max_length=200, examples=["Write report"])
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Priority] = Priority.medium
    due_date: Optional[date] = None
    due_datetime: Optional[datetime] = None
    assigned_to_email: Optional[str] = None

    _v_title = field_validator("title")(_clean_title)


class TaskUpdate(BaseModel):
    """All fields optional (partial update)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None
    due_datetime: Optional[datetime] = None
    assigned_to_email: Optional[str] = None

    _v_title = field_validator("title")(_clean_title)


class SubtaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    position: int = 0
    created_at: Optional[datetime] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: Priority = Priority.medium
    due_date: Optional[date] = None
    due_datetime: Optional[datetime] = None
    created_at: Optional[datetime] = None
    user_id: int
    assigned_to_id: Optional[int] = None
    assigned_to_email: Optional[str] = None
    assigned_by_id: Optional[int] = None
    is_overdue: Optional[bool] = None
    subtasks: Optional[List[SubtaskOut]] = []
    subtask_completion: Optional[dict] = None
    deadline_info: Optional[dict] = None


class TaskFilter(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    sort_by: Optional[str] = "created_at"


class ErrorResponse(BaseModel):
    detail: str


# -- Feature 5: Search/Filter -------------------------------------------------

class TaskFilterRequest(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None


class TaskListResponse(BaseModel):
    total: int
    count: int
    tasks: List[TaskOut]


# -- Feature 7: Task Activity -------------------------------------------------

class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    user_email: Optional[str] = None
    created_at: Optional[datetime] = None


class ActivitySummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    task_title: Optional[str] = None
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: Optional[datetime] = None


# -- Feature 8: Subtasks ------------------------------------------------------

class SubtaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class SubtaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    position: Optional[int] = None


# -- Feature 9: Collaboration -------------------------------------------------

class ShareTaskRequest(BaseModel):
    email: str
    permission: str = "view"

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, v: str) -> str:
        if v not in ("view", "edit", "comment"):
            raise ValueError("Permission must be 'view', 'edit', or 'comment'")
        return v


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_email: Optional[str] = None
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# -- Feature A: Enhanced Collaboration ----------------------------------------

class AssignTaskRequest(BaseModel):
    email: str


class AddCollaboratorRequest(BaseModel):
    email: str
    role: CollaboratorRole = CollaboratorRole.viewer

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: CollaboratorRole) -> CollaboratorRole:
        if v not in (CollaboratorRole.owner, CollaboratorRole.manager,
                     CollaboratorRole.contributor, CollaboratorRole.viewer):
            raise ValueError("Invalid role")
        return v


class CollaboratorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    user_email: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: Optional[int] = None
    type: str
    message: str
    read: bool = False
    created_at: Optional[datetime] = None
