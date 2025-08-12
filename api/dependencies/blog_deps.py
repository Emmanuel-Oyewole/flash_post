from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db_session
from ..blogs.service import BlogService
from ..shared.blog_repo import BlogRepository
from ..shared.tag_repo import TagRepository
from ..shared.user_repo import UserRepository
from .auth_dep import get_user_repo
from .tag_deps import get_tag_repo


async def get_blog_repo(db: AsyncSession = Depends(get_db_session)) -> BlogRepository:
    return BlogRepository(db)


async def get_blog_service(
    blog_repo: BlogRepository = Depends(get_blog_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> BlogService:

    return BlogService(blog_repo, tag_repo, user_repo)
