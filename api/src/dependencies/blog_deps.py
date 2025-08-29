from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db_session
from ..blogs.service import BlogService
from ..shared.blog_repo import BlogRepository
from ..shared.tag_repo import TagRepository
from ..shared.user_repo import UserRepository

# from .auth_dep import get_user_repo
# from .tag_deps import get_tag_repo


# async def get_blog_repo(db: AsyncSession = Depends(get_db_session)) -> BlogRepository:
#     return BlogRepository(db)


async def get_blog_service(db: AsyncSession = Depends(get_db_session)) -> BlogService:
    blog_repo = BlogRepository(db)
    tag_repo = TagRepository(db)
    user_repo = UserRepository(db)

    return BlogService(blog_repo, tag_repo, user_repo)
