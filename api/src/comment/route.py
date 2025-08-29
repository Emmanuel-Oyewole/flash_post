from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from .schema import CommentCreate, CommentUpdate, CommentResponse
from .service import CommentService
from ..like.service import LikeService
from ..models import User
from ..dependencies.auth_dep import get_current_user
from ..dependencies.comment_deps import get_comment_service
from ..dependencies.like_deps import get_like_service
from ..exceptions.exceptions import UnExpectedError
from ..shared.pagination import PaginationParams, PaginatedResponse


router = APIRouter(prefix="/blog", tags=["Comments"])


@router.post(
    "/{blog_id}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    data: CommentCreate,
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Creates a comment on a specified blog post.
    """
    try:
        return await comment_service.create_comment(
            blog_id=blog_id, author_id=current_user.id, data=data
        )
    except Exception as e:
        raise e


@router.get(
    "/{blog_id}/comments",
    response_model=PaginatedResponse[CommentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_comments(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Returns a paginated list of comments for the specified blog post.
    """
    pagination = PaginationParams(page=page, per_page=per_page)
    try:
        return await comment_service.list_comments(blog_id, pagination)
    except Exception as e:
        raise e


@router.get(
    "/{blog_id}/comments/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_comment(
    comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Returns a single comment by its ID.
    """
    try:
        return await comment_service.get_comment(comment_id)
    except Exception as e:
        raise e


@router.put(
    "/{blog_id}/comment/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_comment(
    data: CommentUpdate,
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Updates a specific comment on the specified blog post.
    """
    try:
        return await comment_service.update_comment(
            comment_id=comment_id, blog_id=blog_id, data=data, user_id=current_user.id
        )
    except Exception as e:
        raise e


@router.delete(
    "/{blog_id}/comment/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Deletes a specific comment from the specified blog post.
    Only the comment author or admin can delete comments.
    """
    try:
        await comment_service.delete_comment(blog_id, comment_id, current_user.id)
    except Exception as e:
        raise e


@router.post(
    "/{blog_id}/comment/{parent_comment_id}/reply",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reply_to_comment(
    data: CommentCreate,
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    parent_comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Creates a reply to a specific comment on the specified blog post.
    """
    try:
        return await comment_service.create_reply(
            blog_id=blog_id,
            parent_comment_id=parent_comment_id,
            author_id=current_user.id,
            data=data,
        )
    except Exception as e:
        raise e


@router.get(
    "/{blog_id}/comment/{parent_comment_id}/replies",
    response_model=PaginatedResponse[CommentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_replies(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    parent_comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Returns a paginated list of replies to a specific comment on the specified blog post.
    """
    try:
        pagination = PaginationParams(page=page, per_page=per_page)
        return await comment_service.get_replies(
            blog_id=str(blog_id),
            parent_comment_id=str(parent_comment_id),
            pagination=pagination,
            user_id=str(current_user.id) if current_user else None,
        )
    except Exception as e:
        raise e


@router.put(
    "{blog_id}/comment/{parent_comment_id}/reply/{reply_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_reply(
    data: CommentUpdate,
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    parent_comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    reply_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Update a reply (author or admin only)."""
    try:
        return await comment_service.update_reply(
            blog_id=blog_id,
            parent_comment_id=parent_comment_id,
            reply_id=reply_id,
            user_id=current_user.id,
            data=data,
        )
    except Exception as e:
        raise e


@router.delete(
    "{blog_id}/comment/{parent_comment_id}/reply/{reply_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_reply(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    parent_comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    reply_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Delete a reply (author or admin only)."""
    try:
        await comment_service.delete_reply(
            blog_id=blog_id,
            reply_id=reply_id,
            user_id=current_user.id,
            parent_comment_id=parent_comment_id,
        )
    except Exception as e:
        raise e


@router.post("/comment/{comment_id}/like")
async def like_comment(
    comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service),
):
    """
    Likes a specific comment.
    """
    try:
        return await like_service.like(current_user.id, comment_id, "comment")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/comment/{comment_id}/unlike")
async def unlike_comment(
    comment_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service),
):
    """
    Unlikes a specific comment.
    """
    try:
        return await like_service.unlike(current_user.id, comment_id, "comment")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
