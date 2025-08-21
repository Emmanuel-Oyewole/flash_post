from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from ..models import User
from .schema import TagResponse, TagCreate
from ..shared.pagination import PaginatedResponse, PaginationParams
from ..dependencies.auth_dep import get_current_user
from ..dependencies.tag_deps import get_tag_service
from .service import TagService
# from ..dependencies.blog_deps import get_blog_service
# from ..blogs.service import BlogService


router = APIRouter(prefix="/tag", tags=["Tags"])


@router.get(
    "/tags",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[TagResponse],
)
async def get_tags(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search_query: Optional[str] = Query(None, alias="q", description="Search query"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    sort_by: str = Query("usage_count", regex="^(name|usage_count|created_at)$"),
    tag_service: TagService = Depends(get_tag_service),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of tags.
    """
    pagination = PaginationParams(page=page, per_page=per_page)

    return await tag_service.list_tags(search_query, sort_by, order, pagination)


@router.post("/tags", status_code=status.HTTP_201_CREATED, response_model=TagResponse)
async def create_tag(
    tag: TagCreate,
    tag_service: TagService = Depends(get_tag_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tag.
    """
    try:
        return await tag_service.create_tag(tag, current_user)
    except Exception as e:
        raise e


@router.get(
    "/tags/{tag_id}", status_code=status.HTTP_200_OK, response_model=TagResponse
)
async def get_tag(
    tag_id: str,
    tag_service: TagService = Depends(get_tag_service),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific tag by its ID.
    """
    try:
        return await tag_service.get_tag_by_id(tag_id)
    except Exception as e:
        raise e


@router.put(
    "/tags/{tag_id}", status_code=status.HTTP_200_OK, response_model=TagResponse
)
async def update_tag(
    tag_id: str,
    tag_data: TagCreate,
    tag_service: TagService = Depends(get_tag_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing tag by its ID.
    """
    try:
        return await tag_service.update_tag(tag_id, tag_data, current_user)
    except Exception as e:
        raise e


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    tag_service: TagService = Depends(get_tag_service),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a tag by its ID.
    """
    try:
        await tag_service.delete_tag(tag_id, current_user)
    except Exception as e:
        raise e
