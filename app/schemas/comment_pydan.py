

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentResponse(BaseModel):
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CommentCreateModel(BaseModel):
    content: str