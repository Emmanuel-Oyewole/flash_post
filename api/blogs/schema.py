from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import Query
from typing import List, Optional
from datetime import datetime
import uuid
from ..user.schema import PublicUser

# from ..tag.schema import TagBase
from ..tag.schema import TagResponse
from ..shared.schema import PublicCommentResponse


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Blog title")
    content: str = Field(..., min_length=1, description="Blog content")
    tags: Optional[List[str]] = Field(default=[], description="List of tag names")
    is_published: bool = Field(
        default=False, description="Publish immediately or save as draft"
    )

    @field_validator("title")
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    @field_validator("content")
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v.strip()

    @field_validator("tags")
    def validate_tags(cls, v):
        if v:
            # Remove duplicates and empty tags
            cleaned_tags = list(set([tag.strip() for tag in v if tag.strip()]))
            if len(cleaned_tags) > 10:  # Reasonable limit
                raise ValueError("Maximum 10 tags allowed")
            return cleaned_tags
        return []


class BlogResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    slug: str
    comments: Optional[List[PublicCommentResponse]] = []
    is_published: bool
    view_count: int
    like_count: int
    comment_count: int
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    author: PublicUser
    tags: Optional[List[TagResponse]] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class BlogCreate(BaseModel):
    """Schema for creating a new blog."""

    title: str = Field(..., min_length=1, max_length=255, description="Blog title")
    content: str = Field(
        ..., min_length=1, max_length=50000, description="Blog content (plain text)"
    )
    # summary: Optional[str] = Field(
    #     None, max_length=500, description="Brief blog summary"
    # )
    tags: List[str] = Field(default=[], description="List of tag names")
    is_published: bool = Field(default=False, description="Whether blog is published")

    @field_validator("title")
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("content")
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

    # @field_validator("summary")
    # def summary_must_not_be_empty(cls, v):
    #     if v is not None and not v.strip():
    #         raise ValueError("Summary cannot be empty")
    #     return v.strip() if v else None

    @field_validator("tags")
    def validate_tags(cls, v):
        if v is None:
            return []
        # Remove duplicates, empty strings, and limit length
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                tag_clean = tag.strip()
                if len(tag_clean) > 50:
                    raise ValueError(f'Tag "{tag_clean}" exceeds 50 character limit')
                if tag_clean not in cleaned_tags:
                    cleaned_tags.append(tag_clean)

        if len(cleaned_tags) > 10:
            raise ValueError("Maximum 10 tags allowed per blog")

        return cleaned_tags


class BlogUpdate(BaseModel):
    """Schema for updating an existing blog."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated blog title"
    )
    content: Optional[str] = Field(
        None, min_length=1, max_length=50000, description="Updated blog content"
    )
    tags: Optional[List[str]] = Field(None, description="Updated list of tag names")
    is_published: Optional[bool] = Field(None, description="Updated publish status")

    @field_validator("title")
    def title_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None

    @field_validator("content")
    def content_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip() if v else None

    # @field_validator("summary")
    # def summary_must_not_be_empty(cls, v):
    #     if v is not None and not v.strip():
    #         raise ValueError("Summary cannot be empty")
    #     return v.strip() if v else None

    @field_validator("tags")
    def validate_tags(cls, v):
        if v is None:
            return None
        # Same validation as BlogCreate
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                tag_clean = tag.strip()
                if len(tag_clean) > 50:
                    raise ValueError(f'Tag "{tag_clean}" exceeds 50 character limit')
                if tag_clean not in cleaned_tags:
                    cleaned_tags.append(tag_clean)

        if len(cleaned_tags) > 10:
            raise ValueError("Maximum 10 tags allowed per blog")

        return cleaned_tags


class BlogFilters(BaseModel):
    """Schema for blog filtering parameters."""

    author_id: Optional[str] = Field(None, description="Filter by author ID")
    tag_names: Optional[List[str]] = Field(None, description="Filter by tag names")
    is_published: Optional[bool] = Field(None, description="Filter by published status")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    search_query: Optional[str] = Field(None, description="Search in title and content")
    include_drafts: bool = Field(default=False, description="Include draft posts")
    viewer_id: Optional[str] = Field(
        None, description="Current user ID for permission checks"
    )


class AuthorResponse(BaseModel):
    """Schema for author data in blog responses."""

    id: str
    username: str
    display_name: Optional[str]
    profile_picture_url: Optional[str]

    class Config:
        from_attributes = True


class BlogListResponse(BaseModel):
    """Schema for blog list item (without full content)."""

    id: uuid.UUID
    title: str
    content: str
    comments: Optional[List[PublicCommentResponse]] = []
    # summary: str
    slug: str
    author: PublicUser
    tags: Optional[List[TagResponse]] = []
    is_published: bool
    # is_featured: bool
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    published_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
