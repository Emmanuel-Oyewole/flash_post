from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from ..user.model import User
from ..dependencies.blog_deps import get_blog_service
from ..dependencies.auth_dep import get_current_user
from .service import BlogService
from .schema import BlogCreate, BlogListResponse, BlogResponse, BlogFilters
from ..shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/blog", tags=["Blogs"])


@router.post("/", response_model=BlogResponse)
async def create_blog(
    payload: BlogCreate,
    current_user: User = Depends(get_current_user),
    blog_service: BlogService = Depends(get_blog_service),
):
    try:
        new_blog = await blog_service.create_blog(payload, current_user.id)

        return new_blog

    except Exception as e:
        raise e


@router.get("/public-blog")
async def public_list_blogs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filter parameters
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    tag_names: Optional[List[str]] = Query(None, description="Filter by tag names"),
    # is_featured: Optional[bool] = Query(None, description="Filter featured blogs"),
    search_query: Optional[str] = Query(None, description="Search in title/content"),
    # Dependencies
    blog_service: BlogService = Depends(get_blog_service),
):
    """
    List blogs with filtering and pagination.
    Returns summary data without full content for performance.
    """

    filters = BlogFilters(
        author_id=author_id,
        tag_names=tag_names or [],
        # is_featured=is_featured,
        search_query=search_query,
        is_published=True,  # Only published blogs in public list
        include_drafts=False,
    )

    pagination = PaginationParams(page=page, per_page=per_page)

    return await blog_service.list_blogs(filters=filters, pagination=pagination)


@router.get("/", response_model=PaginatedResponse[BlogListResponse])
async def auth_list_blogs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filter parameters
    tag_names: Optional[List[str]] = Query(None, description="Filter by tag names"),
    # is_featured: Optional[bool] = Query(None, description="Filter featured blogs"),
    search_query: Optional[str] = Query(None, description="Search in title/content"),
    is_published: Optional[bool] = Query(True, description="Add published blog"),
    include_drafts: Optional[bool] = Query(True, description="Add draft blog"),
    # Dependencies
    blog_service: BlogService = Depends(get_blog_service),
    current_user: User = Depends(get_current_user),
):
    """
    List blogs with filtering and pagination.
    Returns summary data without full content for performance.
    For authenticated user
    """

    filters = BlogFilters(
        tag_names=tag_names or [],
        # is_featured=is_featured,
        search_query=search_query,
        is_published=is_published,
        include_drafts=include_drafts,
    )

    pagination = PaginationParams(page=page, per_page=per_page)

    return await blog_service.list_blogs(
        filters=filters, pagination=pagination, user_id=current_user.id
    )


@router.get("/{blog_id}")
async def get_blog(
    blog_id: str,
    blog_service: BlogService = Depends(get_blog_service),
    current_user: User = Depends(get_current_user),
):
    try:
        return await blog_service.get_blog_by_id(blog_id, current_user.id)
    except Exception as e:
        raise e


@router.get("/slug/{slug}")
async def get_blog_by_slug(slug: str):
    return f"Get blog by slug endpoint: {slug}"


@router.put("/{blog_id}")
async def update_blog(blog_id: str):
    return f"Update blog endpoint: {blog_id}"


@router.delete("/{blog_id}")
async def delete_blog(blog_id: str):
    return f"Delete blog endpoint: {blog_id}"


@router.post("/{blog_id}/publish")
async def publish_blog(blog_id: str):
    return f"Publish blog endpoint: {blog_id}"


@router.post("/{blog_id}/unpublish")
async def unpublish_blog(blog_id: str):
    return f"Unpublish blog endpoint: {blog_id}"
