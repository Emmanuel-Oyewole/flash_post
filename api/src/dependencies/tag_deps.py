from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db_session
from ..shared.tag_repo import TagRepository
from ..tag.service import TagService


async def get_tag_repo(db: AsyncSession = Depends(get_db_session)) -> TagRepository:

    return TagRepository(db)


def get_tag_service(db: AsyncSession = Depends(get_db_session)) -> TagService:
    tag_repo = TagRepository(db)

    return TagService(tag_repo)
