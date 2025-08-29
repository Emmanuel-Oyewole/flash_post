from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..comment.service import CommentService
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..shared.like_repo import LikeRepository
from ..like.service import LikeService
from ..config.database import get_db_session


def get_like_service(db: AsyncSession = Depends(get_db_session)) -> CommentService:
    """
    Instantiates the comment service
    """
    like_repo = LikeRepository(db)
    blog_repo = BlogRepository(db)
    comment_repo = CommentRepository(db)

    return LikeService(like_repo=like_repo, blog_repo=blog_repo, comment_repo=comment_repo)
