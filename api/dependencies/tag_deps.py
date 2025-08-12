from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db_session
from ..shared.tag_repo import TagRepository

async def get_tag_repo(db: AsyncSession = Depends(get_db_session)) -> TagRepository:
    
    return TagRepository(db)