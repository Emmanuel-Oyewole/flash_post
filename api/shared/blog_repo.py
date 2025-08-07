from sqlalchemy.ext.asyncio import AsyncSession

class BlogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
