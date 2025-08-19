from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, asc

from ..tag.model import Tag
from ..shared.pagination import PaginationParams, PaginatedResponse



class TagRepository:
    """Repository for tag-related database operations."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def get_by_id(self, tag_id: str) -> Optional[Tag]:
        """Get tag by ID."""
        return self.db.query(Tag).filter(Tag.id == tag_id).first()

    async def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name (case-insensitive)."""
        return await self.db.query(Tag).filter(
            func.lower(Tag.name) == name.lower()
        ).first()

    def get_by_slug(self, slug: str) -> Optional[Tag]:
        """Get tag by slug."""
        return self.db.query(Tag).filter(Tag.slug == slug).first()

    def get_by_names(self, names: List[str]) -> List[Tag]:
        """
        Get multiple tags by their names (case-insensitive).
        Used by BlogService to validate tag existence.
        """
        if not names:
            return []
        
        # Normalize names to lowercase for comparison
        normalized_names = [name.lower() for name in names]
        
        return self.db.query(Tag).filter(
            func.lower(Tag.name).in_(normalized_names)
        ).all()

    def get_by_ids(self, tag_ids: List[str]) -> List[Tag]:
        """Get multiple tags by their IDs."""
        if not tag_ids:
            return []
        
        return self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()

    def create(self, tag_data: Dict[str, Any]) -> Tag:
        """Create a new tag."""
        tag = Tag(**tag_data)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag_id: str, updates: Dict[str, Any]) -> Optional[Tag]:
        """Update existing tag."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return None
        
        for key, value in updates.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
        
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag_id: str) -> bool:
        """Delete tag by ID."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return False
        
        self.db.delete(tag)
        self.db.commit()
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

    def list_tags(
        self, 
        search_query: Optional[str] = None,
        sort_by: str = "usage_count",
        order: str = "desc",
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[Tag]:
        """List tags with optional filtering, sorting, and pagination."""
        query = self.db.query(Tag)
        
        # Apply search filter
        if search_query:
            search_term = f"%{search_query.lower()}%"
            query = query.filter(
                func.lower(Tag.name).like(search_term)
            )
        
        # Apply sorting
        sort_column = getattr(Tag, sort_by, Tag.usage_count)
        if order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.per_page
            query = query.offset(offset).limit(pagination.per_page)
        
        tags = query.all()
        
        return PaginatedResponse.create(
            items=tags,
            total=total,
            page=pagination.page if pagination else 1,
            per_page=pagination.per_page if pagination else total
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

    def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        """Check if tag slug exists (for uniqueness validation)."""
        query = self.db.query(Tag).filter(Tag.slug == slug)
        
        if exclude_id:
            query = query.filter(Tag.id != exclude_id)
        
        return query.first() is not None
