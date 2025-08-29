from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator, Field


class TagBase(BaseModel):
    name: str | None
    slug: str | None
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color
    usage_count: int = 0
    created_at: Optional[datetime] = None


class TagCreate(BaseModel):
    """Schema for creating a new tag."""

    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(
        None, max_length=255, description="Tag description"
    )
    color: Optional[str] = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip() if v else None


class TagResponse(BaseModel):
    """Schema for tag responses."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagUpdate(BaseModel):
    """Schema for updating a tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip() if v else None

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip() if v else None
