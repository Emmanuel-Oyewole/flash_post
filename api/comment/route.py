from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from .schema import CommentCreate, CommentUpdate
from .service import CommentService
from ..models import User
from ..dependencies.auth_dep import get_current_user
from ..dependencies.comment_deps import get_comment_service
from ..exceptions.exceptions import UnExpectedError
from ..shared.pagination import PaginationParams


router = APIRouter(prefix="/blog", tags=["Comments"])


@router.post("/{blog_id}/comment")
async def create_comment(
    blog_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Creates a comment on the specified blog post.
    """
    try:
        return await comment_service.create_comment(
            blog_id=blog_id, author_id=current_user.id, data=data
        )
    except Exception as e:
        raise e


@router.get("/{blog_id}/comments")
async def get_comments(
    blog_id: str,
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


@router.get("/{blog_id}/comments/{comment_id}")
async def get_comment(
    blog_id: str,
    comment_id: str,
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


@router.put("/{blog_id}/comment/{comment_id}")
async def update_comment(
    blog_id: str,
    comment_id: str,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Updates a specific comment on the specified blog post.
    """
    try:
        return await comment_service.update_comment(comment_id=comment_id,blog_id=blog_id,data=data, user_id=current_user.id )
    except Exception as e:
        raise e


@router.delete("/{blog_id}/comment/{comment_id}")
async def delete_comment(
    blog_id: str,
    comment_id: str,
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


@router.post("/{blog_id}/comment/{comment_id}/reply")
async def reply_to_comment(
    blog_id: str,
    comment_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """
    Creates a reply to a specific comment on the specified blog post.
    """
    try:
        # parent_comment = await comment_service.get_comment(comment_id)
        # return await comment_service.create_comment(
        #     parent_comment.blog_id, current_user.id, data, comment_id
        # )

        return await comment_service.create_reply(
            blog_id=str(blog_id),
            comment_id=str(comment_id),
            author_id=str(current_user.id),
            data=data,
        )
    except Exception as e:
        raise e


@router.get("/{blog_id}/comment/{comment_id}/replies")
async def get_replies(
    blog_id: str,
    comment_id: str,
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
            comment_id=str(comment_id),
            pagination=pagination,
            user_id=str(current_user.id) if current_user else None
        )
    except Exception as e:
        raise e
    
@router.put("{blog_id}/reply/{reply_id}")
async def update_reply(
    blog_id: str,
    reply_id: str,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Update a reply (author or admin only)."""
    try:
        return await comment_service.update_reply(
            blog_id=str(blog_id),
            reply_id=str(reply_id),
            user_id=str(current_user.id),
            data=data
        )
    except Exception as e:
        raise e
    
@router.delete("{blog_id}/reply/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reply(
    blog_id: str,
    reply_id: str,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Delete a reply (author or admin only)."""
    try:
        await comment_service.delete_reply(
            blog_id=str(blog_id),
            reply_id=str(reply_id),
            user_id=str(current_user.id)
        )
    except Exception as e:
        raise e


# @router.post("/{blog_id}/comment/{comment_id}/like")
# async def like_comment(blog_id: str, comment_id: str):
#     """
#     Likes a specific comment on the specified blog post.
#     """
#     return f"Like comment {comment_id} on blog {blog_id} endpoint"


# @router.delete("/{blog_id}/comment/{comment_id}/unlike")
# async def unlike_comment(blog_id: str, comment_id: str):
#     """
#     Unlikes a specific comment on the specified blog post.
#     """
#     return f"Unlike comment {comment_id} on blog {blog_id} endpoint"
