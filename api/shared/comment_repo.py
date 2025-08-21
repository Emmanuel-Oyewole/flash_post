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
