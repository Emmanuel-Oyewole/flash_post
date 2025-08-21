from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, asc, select

from ..tag.model import Tag
from ..shared.pagination import PaginationParams, PaginatedResponse


class TagRepository:
    """Repository for tag-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, tag_id: str) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.id == tag_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Tag]:
        stmt = select(Tag).where(func.lower(Tag.name) == name.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Tag]:
        stmt = select(Tag).where(Tag.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_names(self, names: List[str]) -> List[Tag]:
        if not names:
            return []
        normalized_names = [name.lower() for name in names]
        stmt = select(Tag).where(func.lower(Tag.name).in_(normalized_names))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_ids(self, tag_ids: List[str]) -> List[Tag]:
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.id.in_(tag_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, tag_data: Dict[str, Any]) -> Tag:
        tag = Tag(**tag_data)
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def update(self, tag_id: str, updates: Dict[str, Any]) -> Optional[Tag]:
        tag = await self.get_by_id(tag_id)
        if not tag:
            return None
        for key, value in updates.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete(self, tag_id: str) -> bool:
        tag = await self.get_by_id(tag_id)
        if not tag:
            return False
        await self.db.delete(tag)
        await self.db.commit()
        return True

    def increment_usage_count(self, tag_id: str, increment: int = 1) -> None:
        """Increment tag usage count."""
        self.db.query(Tag).filter(Tag.id == tag_id).update({
            Tag.usage_count: Tag.usage_count + increment
        })
        # Note: Don't commit here - let the calling transaction handle it

    def increment_usage_counts(self, tag_ids: List[str], increment: int = 1) -> None:
        """Increment usage count for multiple tags."""
        if not tag_ids:
            return

        self.db.query(Tag).filter(Tag.id.in_(tag_ids)).update({
            Tag.usage_count: Tag.usage_count + increment
        }, synchronize_session=False)
        # Note: Don't commit here - let the calling transaction handle it

    def decrement_usage_counts(self, tag_ids: List[str], decrement: int = 1) -> None:
        """Decrement usage count for multiple tags."""
        if not tag_ids:
            return

        self.db.query(Tag).filter(Tag.id.in_(tag_ids)).update({
            Tag.usage_count: func.greatest(Tag.usage_count - decrement, 0)
        }, synchronize_session=False)
        # Note: Don't commit here - let the calling transaction handle it

    async def list_tags(
        self,
        search_query: Optional[str] = None,
        sort_by: str = "usage_count",
        order: str = "desc",
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse[Tag]:
        stmt = select(Tag)
        # Search filter
        if search_query:
            search_term = f"%{search_query.lower()}%"
            stmt = stmt.where(func.lower(Tag.name).like(search_term))
        # Sorting
        sort_column = getattr(Tag, sort_by, Tag.usage_count)
        stmt = stmt.order_by(
            desc(sort_column) if order.lower() == "desc" else asc(sort_column)
        )
        # Count total
        count_stmt = select(func.count(Tag.id))
        if search_query:
            count_stmt = count_stmt.where(func.lower(Tag.name).like(search_term))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        # Pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.per_page
            stmt = stmt.offset(offset).limit(pagination.per_page)
        result = await self.db.execute(stmt)
        tags = result.scalars().all()
        return PaginatedResponse.create(
            items=tags,
            total=total,
            page=pagination.page if pagination else 1,
            per_page=pagination.per_page if pagination else len(tags),
        )

    def get_popular_tags(self, limit: int = 10) -> List[Tag]:
        """Get most popular tags by usage count."""
        return self.db.query(Tag).order_by(desc(Tag.usage_count)).limit(limit).all()

    def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if tag name exists (for uniqueness validation)."""
        query = self.db.query(Tag).filter(func.lower(Tag.name) == name.lower())

        if exclude_id:
            query = query.filter(Tag.id != exclude_id)

        return query.first() is not None

    async def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        stmt = select(Tag).where(Tag.slug == slug)
        if exclude_id:
            stmt = stmt.where(Tag.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
