from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..comment.service import CommentService
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..shared.user_repo import UserRepository
from ..config.database import get_db_session


def get_comment_service(db: AsyncSession = Depends(get_db_session)) -> CommentService:
    """
    Instantiates the comment service
    """
    comment_repo = CommentRepository(db)
    blog_repo = BlogRepository(db)
    user_repo = UserRepository(db)

    return CommentService(comment_repo, blog_repo, user_repo)
