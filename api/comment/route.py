from fastapi import APIRouter, Depends, status
from .schema import CommentCreate
from .service import CommentService
from ..models import User
from ..dependencies.auth_dep import get_current_user
from ..dependencies.comment_deps import get_comment_service
from ..exceptions.exceptions import UnExpectedError


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
async def get_comments(blog_id: str):
    """
    Returns a paginated list of comments for the specified blog post.
    """
    return f"Get comments for blog endpoint: {blog_id}"


@router.get("/comments/{comment_id}")
async def get_comment(comment_id: str):
    """
    Returns a single comment by its ID.
    """
    return f"Get comment by ID endpoint: {comment_id}"


@router.put("/{blog_id}/comment/{comment_id}")
async def update_comment(blog_id: str, comment_id: str):
    """
    Updates a specific comment on the specified blog post.
    """
    return f"Update comment {comment_id} on blog {blog_id} endpoint"


@router.delete("/{blog_id}/comment/{comment_id}")
async def delete_comment(blog_id: str, comment_id: str):
    """
    Deletes a specific comment from the specified blog post.
    """
    return f"Delete comment {comment_id} on blog {blog_id} endpoint"


@router.post("/{blog_id}/comment/{comment_id}/reply")
async def reply_to_comment(blog_id: str, comment_id: str):
    """
    Creates a reply to a specific comment on the specified blog post.
    """
    return f"Reply to comment {comment_id} on blog {blog_id} endpoint"


@router.get("/{blog_id}/comment/{comment_id}/replies")
async def get_replies(blog_id: str, comment_id: str):
    """
    Returns a paginated list of replies to a specific comment on the specified blog post.
    """
    return f"Get replies for comment {comment_id} on blog {blog_id} endpoint"


@router.post("/{blog_id}/comment/{comment_id}/like")
async def like_comment(blog_id: str, comment_id: str):
    """
    Likes a specific comment on the specified blog post.
    """
    return f"Like comment {comment_id} on blog {blog_id} endpoint"


@router.delete("/{blog_id}/comment/{comment_id}/unlike")
async def unlike_comment(blog_id: str, comment_id: str):
    """
    Unlikes a specific comment on the specified blog post.
    """
    return f"Unlike comment {comment_id} on blog {blog_id} endpoint"
