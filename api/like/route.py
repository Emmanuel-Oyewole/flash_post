from fastapi import APIRouter


router = APIRouter(prefix="/blog", tags=["Likes"])


@router.post("/{blog_id}/like")
async def like_blog(blog_id: str):
    """
    Creates like record, increments blog like count
    """
    return f"Like blog endpoint: {blog_id}"


@router.delete("/{blog_id}/unlike")
async def unlike_blog(blog_id: str):
    """Deletes like record, decrements blog like count"""
    return f"Unlike blog endpoint: {blog_id}"


@router.get("/{blog_id}/likes")
async def get_blog_likes(blog_id: str):
    """
    Returns paginated list of users who liked blog
    """
    return f"Get likes for blog endpoint: {blog_id}"


@router.get("/users/me/likes")
async def get_user_likes():
    """
    Returns paginated list of blogs liked by the user
    """
    return "Get user likes endpoint"


@router.get("/likes/check/{blog_id}")
async def check_blog_like(blog_id: str) -> bool:
    """
    Check if the current user has liked the blog
    """
    return f"Check if blog is liked endpoint: {blog_id}"
