from typing import List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field, UUID4, ConfigDict
from datetime import datetime


class PublicUser(BaseModel):
    id: uuid.UUID
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    email: EmailStr
    avatar: str | None = None
    role: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicCommentResponse(BaseModel):
    id: uuid.UUID
    content: str
    blog_id: uuid.UUID
    author: PublicUser
    author_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    is_edited: bool
    like_count: int
    created_at: datetime
    updated_at: datetime
    replies: Optional[List["PublicCommentResponse"]] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


PublicCommentResponse.model_rebuild()
