from fastapi import APIRouter, Depends, Path, HTTPException, status
from ..models import User
from ..like.service import LikeService
from ..blogs.schema import BlogResponse
from ..dependencies.auth_dep import get_current_user
from ..dependencies.like_deps import get_like_service


router = APIRouter(tags=["Likes"])


@router.post(
    "/{blog_id}/like", response_model=BlogResponse, status_code=status.HTTP_200_OK
)
async def like_blog(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service),
):
    """
    Creates like record, increments blog like count
    """
    try:
        return await like_service.like(current_user.id, blog_id, "blog")
    except Exception as e:
        raise e


@router.delete(
    "/{blog_id}/unlike", response_model=BlogResponse, status_code=status.HTTP_200_OK
)
async def unlike_blog(
    blog_id: str = Path(
        ...,
        regex="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$",
    ),
    current_user: User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service),
):
    """Deletes like record, decrements blog like count"""
    try:
        return await like_service.unlike(current_user.id, blog_id, "blog")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ###############################################
# @router.get("/{blog_id}/likes")
# async def get_blog_likes(blog_id: str):
#     """
#     Returns paginated list of users who liked blog
#     """
#     return f"Get likes for blog endpoint: {blog_id}"


# @router.get("/users/me/likes")
# async def get_user_likes():
#     """
#     Returns paginated list of blogs liked by the user
#     """
#     return "Get user likes endpoint"


# @router.get("/likes/check/{blog_id}")
# async def check_blog_like(blog_id: str) -> bool:
#     """
#     Check if the current user has liked the blog
#     """
#     return f"Check if blog is liked endpoint: {blog_id}"
