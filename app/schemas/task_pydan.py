

from datetime import datetime
import enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.task_mod import TaskPriority, TaskStatus
from app.schemas.comment_pydan import CommentResponse


class TaskSortBy(str, enum.Enum):
    PRIORITY = "priority"
    DEADLINE = "deadline"
    CREATED_AT = "created_at"


class TaskCreateModel(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int | None = None
    deadline: datetime


class TaskDBResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus    
    priority: TaskPriority 
    author_id: int
    assignee_id: int | None
    deadline: datetime
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskFilter(BaseModel):
    search: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    deadline: datetime | None = None
    sort_by: TaskSortBy = TaskSortBy.PRIORITY
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class TaskDetailResponse(TaskDBResponse):
    comments: list[CommentResponse] = []


class TaskUpdateModel(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    deadline: datetime | None = None