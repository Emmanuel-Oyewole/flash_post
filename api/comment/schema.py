from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..shared.schema import PublicUser


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: UUID
    content: str
    blog_id: UUID
    author: PublicUser
    author_id: UUID
    parent_id: Optional[UUID]
    is_edited: bool
    like_count: int
    created_at: datetime
    updated_at: datetime
    replies: Optional[List["CommentResponse"]] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


CommentResponse.model_rebuild()
