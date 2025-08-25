from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload
from ..models import Comment
from ..comment.schema import CommentCreate
from ..shared.pagination import PaginationParams, PaginatedResponse


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
            query = query.options(
                selectinload(Comment.replies), selectinload(Comment.author)
            )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def list_by_blog(
        self, blog_id: str, pagination: PaginationParams, load_relation: bool = True
    ) -> PaginatedResponse[Comment]:
        count_query = select(Comment).where(Comment.blog_id == blog_id)
        total = await self.db.scalar(select(func.count()).select_from(count_query))

        offset = (pagination.page - 1) * pagination.per_page
        query = (
            select(Comment).where(Comment.blog_id == blog_id)
            # .order_by(Comment.created_at)
            # .offset(offset)
            # .limit(pagination.per_page)
        )

        if load_relation:
            query = query.options(
                selectinload(Comment.replies), selectinload(Comment.author)
            )
        query = (
            query.order_by(desc(Comment.created_at))
            .offset(offset)
            .limit(pagination.per_page)
        )
        result = await self.db.execute(query)
        comments = result.scalars().unique().all()

        return PaginatedResponse.create(
            items=comments,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    async def update(
        self, blog_id: str, comment_id: str, user_id: str, content: str
    ) -> Comment:
        stmt = select(Comment).where(
            Comment.id == comment_id,
            Comment.author_id == user_id,
            Comment.blog_id == blog_id,
        )

        result = await self.db.execute(stmt)
        comment = result.scalars().first()

        if not comment:
            return None

        comment.content = content
        comment.is_edited = True
        await self.db.commit()
        await self.db.refresh(comment)

        return comment
    
    async def delete(self, blog_id: str, comment_id: str, user_id: str) -> bool:
        try:
            # 🔍 Find the comment with all conditions
            stmt = select(Comment).where(
                Comment.id == comment_id,
                Comment.author_id == user_id,
                Comment.blog_id == blog_id,
            )
            
            result = await self.db.execute(stmt)
            comment = result.scalar_one_or_none()
            
            if not comment:
                return False
            
            # 🗑️ DELETE: This triggers the cascade!
            await self.db.delete(comment)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise e
