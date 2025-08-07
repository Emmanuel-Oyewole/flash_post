from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import uuid
from ..user.schema import PublicUser
from ..tag.schema import TagBase

class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Blog title")
    content: str = Field(..., min_length=1, description="Blog content")
    tags: Optional[List[str]] = Field(default=[], description="List of tag names")
    is_published: bool = Field(default=False, description="Publish immediately or save as draft")

    @field_validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()

    @field_validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicates and empty tags
            cleaned_tags = list(set([tag.strip() for tag in v if tag.strip()]))
            if len(cleaned_tags) > 10:  # Reasonable limit
                raise ValueError('Maximum 10 tags allowed')
            return cleaned_tags
        return []

class BlogResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    slug: str
    is_published: bool
    view_count: int
    like_count: int
    comment_count: int
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    # Author information
    author: PublicUser  # You might want to create a separate AuthorResponse schema
    
    # Tags information
    tags: List[TagBase]  # List of tag objects

    class Config:
        from_attributes = True