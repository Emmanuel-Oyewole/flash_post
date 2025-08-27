from asyncio.log import logger
from datetime import datetime, timezone
from typing import Optional
from click import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from ..models.like_model import Like
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
            stmt = select(Comment).where(
                Comment.id == comment_id,
                Comment.author_id == user_id,
                Comment.blog_id == blog_id,
            )

            result = await self.db.execute(stmt)
            comment = result.scalar_one_or_none()

            if not comment:
                return False

            await self.db.delete(comment)
            await self.db.commit()

            return True

        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            return False

        except Exception as e:
            await self.db.rollback()
            raise e

    async def create_reply(
        self, blog_id: str, parent_id: str, author_id: str, content: str
    ) -> Comment:
        """Create a reply to an existing comment."""
        try:
            # Validate parent comment exists and belongs to blog
            parent_stmt = select(Comment).where(
                Comment.id == UUID(parent_id), Comment.blog_id == UUID(blog_id)
            )
            parent_result = await self.db.execute(parent_stmt)
            parent_comment = parent_result.scalar_one_or_none()

            if not parent_comment:
                raise ValueError(
                    "Parent comment not found or doesn't belong to this blog"
                )

            # Create reply
            reply_data = {
                "content": content,
                "blog_id": UUID(blog_id),
                "author_id": UUID(author_id),
                "parent_id": UUID(parent_id),
                "is_edited": False,
                "like_count": 0,
            }

            reply = Comment(**reply_data)
            self.db.add(reply)
            await self.db.commit()
            await self.db.refresh(reply)

            # Load relationships
            reply_with_relations = await self.get_by_id_with_relations(str(reply.id))
            return reply_with_relations

        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_by_id_with_relations(self, comment_id: str) -> Optional[Comment]:
        """Get comment with author relationship loaded."""
        stmt = (
            select(Comment)
            .options(selectinload(Comment.author), selectinload(Comment.replies))
            .where(Comment.id == UUID(comment_id))
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_replies(
        self,
        comment_id: str,
        pagination: PaginationParams,
        user_id: Optional[str] = None,
    ) -> PaginatedResponse[Comment]:
        """Get paginated replies for a comment."""
        # Count total replies
        count_stmt = select(func.count(Comment.id)).where(
            Comment.parent_id == UUID(comment_id)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # Get paginated replies with author
        stmt = (
            select(Comment)
            .options(selectinload(Comment.author), selectinload(Comment.replies))
            .where(Comment.parent_id == UUID(comment_id))
            .order_by(Comment.created_at)
            .offset((pagination.page - 1) * pagination.per_page)
            .limit(pagination.per_page)
        )

        result = await self.db.execute(stmt)
        replies = result.scalars().all()

        # Add like status if user provided
        # if user_id:
        #     for reply in replies:
        #         reply.is_liked_by_user = await self.is_liked_by_user(
        #             str(reply.id), user_id, "comment"
        #         )

        return PaginatedResponse.create(
            items=replies,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    async def update_reply(
        self, reply_id: str, parent_comment_id: str, author_id: str, content: str
    ) -> Optional[Comment]:
        """Update a reply (author or admin only)."""
        stmt = (
            select(Comment)
            .options(selectinload(Comment.author), selectinload(Comment.replies))
            .where(
                Comment.id == UUID(reply_id),
                Comment.author_id == UUID(author_id),
                Comment.parent_id == UUID(parent_comment_id),
            )
        )

        result = await self.db.execute(stmt)
        reply = result.scalar_one_or_none()

        if not reply:
            return None

        # Update content
        reply.content = content
        reply.is_edited = True
        reply.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        return reply

    async def delete_reply(
        self, reply_id: str, author_id: str, parent_comment_id: str
    ) -> bool:
        """Delete a reply (author or admin only)."""
        stmt = select(Comment).where(
            Comment.id == UUID(reply_id),
            Comment.author_id == UUID(author_id),
            Comment.parent_id == UUID(parent_comment_id),
        )

        result = await self.db.execute(stmt)
        # Use .scalar_one_or_none() to get the Comment object.
        comment_to_delete = result.scalar_one_or_none()

        if comment_to_delete:
            # 2. If the comment exists, pass the object to the `delete()` method.
            await self.db.delete(comment_to_delete)
            # 3. Commit the changes to the database.
            await self.db.commit()
            return True

        return False

    # async def get_like(
    #     self, target_id: str, user_id: str, target_type: str
    # ) -> Optional[Like]:
    #     """Get like by user for comment or blog."""
    #     if target_type == "comment":
    #         stmt = select(Like).where(
    #             Like.comment_id == UUID(target_id), Like.user_id == UUID(user_id)
    #         )
    #     else:
    #         stmt = select(Like).where(
    #             Like.blog_id == UUID(target_id), Like.user_id == UUID(user_id)
    #         )

    #     result = await self.db.execute(stmt)
    #     return result.scalar_one_or_none()

    # async def is_liked_by_user(
    #     self, target_id: str, user_id: str, target_type: str
    # ) -> bool:
    #     """Check if user has liked a comment or blog."""
    #     like = await self.get_like(target_id, user_id, target_type)
    #     return like is not None
