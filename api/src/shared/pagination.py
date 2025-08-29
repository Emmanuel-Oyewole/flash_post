from typing import List, TypeVar, Generic, Optional
from pydantic import BaseModel, Field, ConfigDict
from math import ceil

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response that can be reused for any entity type."""
    items: List[T] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items matching filters")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response with calculated fields."""
        total_pages = ceil(total / per_page) if per_page > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

class PaginationParams(BaseModel):
    """Standard pagination parameters for all endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")