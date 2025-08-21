from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import Comment
from ..comment.schema import CommentCreate


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, comment_data: CommentCreate) -> Comment:
        comment = Comment(**comment_data)
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: str, load_relation: bool = True) -> Comment:

        query = select(Comment).where(Comment.id == comment_id)

        if load_relation:
            query = query.options(selectinload(Comment.replies), selectinload(Comment.author))

        result = await self.db.execute(query)

        return result.scalar_one_or_none()
