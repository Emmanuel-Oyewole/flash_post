from typing import List, Optional, Dict, Any
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, desc, asc, text, select, insert, update
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from datetime import datetime

from api.blogs.model import Blog
from ..tag.model import Tag
from ..user.model import User
from ..blogs.schema import BlogFilters
from ..shared.pagination import PaginationParams, PaginatedResponse
from ..tag.model import blog_tags  # Association table


class BlogRepository:
    """Repository for blog-related database operations with transaction support."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, blog_id: str, include_drafts: bool = False, load_relations: bool = True
    ) -> Optional[Blog]:
        """
        Get blog by ID with optional relationship loading.

        Args:
            blog_id: Blog identifier
            include_drafts: Whether to include unpublished blogs
            load_relations: Whether to eager load author and tags
        """
        query = select(Blog).filter(Blog.id == blog_id)

        # Optional filtering for drafts
        if not include_drafts:
            query = query.filter(Blog.is_published.is_(True))

        # Eager load relationships to avoid N+1 queries
        if load_relations:
            # Use selectinload for efficient eager loading with async sessions
            query = query.options(selectinload(Blog.author), selectinload(Blog.tags))

        # Execute the query asynchronously and get the result
        result = await self.db.execute(query)

        # Get the single result or None if not found
        blog = result.scalar_one_or_none()

        return blog

    def get_by_slug(
        self, slug: str, include_drafts: bool = False, load_relations: bool = True
    ) -> Optional[Blog]:
        """
        Get blog by slug with optional relationship loading.
        """
        query = self.db.query(Blog)

        # Eager load relationships
        if load_relations:
            query = query.options(joinedload(Blog.author), selectinload(Blog.tags))

        # Apply slug filter
        query = query.filter(Blog.slug == slug)

        # Filter by published status if needed
        if not include_drafts:
            query = query.filter(Blog.is_published == True)

        return query.first()

    async def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if slug exists globally (for uniqueness validation).

        Args:
            slug: Slug to check
            exclude_id: Blog ID to exclude from check (for updates)
        """
        # Create the select statement
        query = select(Blog).filter(Blog.slug == slug)

        if exclude_id:
            query = query.filter(Blog.id != exclude_id)

        # Execute the query and get the result
        result = await self.db.execute(query)

        # Fetch the first object, or None if no results
        blog = result.scalars().first()

        return blog is not None

    async def create_blog(self, blog_data: Dict[str, Any]) -> Blog:
        """
        Create a blog record (without tags).
        Used internally by create_with_tags.
        """
        blog = Blog(**blog_data)
        self.db.add(blog)
        await self.db.flush()  # Flush to get the ID, but don't commit
        return blog

    async def create_with_tags(
        self, blog_data: Dict[str, Any], tag_ids: List[str]
    ) -> Blog:
        """
        Create blog with tags in a single transaction.
        This is the main method used by BlogService.

        Args:
            blog_data: Blog data dictionary
            tag_ids: List of tag IDs to associate
        """
        try:
            # Start transaction

            # 1. Create blog record
            blog = await self.create_blog(blog_data)

            # 2. Associate tags if provided
            if tag_ids:
                await self.associate_tags(blog.id, tag_ids)

                # 3. Update tag usage counts
                await self.increment_tag_usage_counts(tag_ids)

            # 4. Commit transaction
            await self.db.commit()

            # 5. Refresh to get all relationships
            await self.db.refresh(blog)

            # 6. Load relationships explicitly
            blog = await self.get_by_id(
                blog.id, include_drafts=True, load_relations=True
            )

            return blog

        except IntegrityError as e:
            await self.db.rollback()
            if "slug" in str(e):
                raise ValueError(f"Slug already exists: {blog_data.get('slug')}")
            raise e
        except Exception as e:
            await self.db.rollback()
            raise e

    def update_blog(self, blog_id: str, updates: Dict[str, Any]) -> Optional[Blog]:
        """
        Update blog record (without tag changes).
        Used internally by update_with_tags.
        """
        blog = self.get_by_id(blog_id, include_drafts=True, load_relations=False)
        if not blog:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(blog, key):
                setattr(blog, key, value)

        # Update timestamp
        blog.updated_at = datetime.utcnow()

        self.db.flush()  # Flush but don't commit (let transaction handle it)
        return blog

    def update_with_tags(
        self,
        blog_id: str,
        updates: Dict[str, Any],
        new_tag_ids: Optional[List[str]] = None,
    ) -> Optional[Blog]:
        """
        Update blog with optional tag replacement in a transaction.

        Args:
            blog_id: Blog identifier
            updates: Dictionary of fields to update
            new_tag_ids: New tag IDs to replace existing ones (None = no change)
        """
        try:
            with self.db.begin():
                # 1. Update blog record
                blog = self.update_blog(blog_id, updates)
                if not blog:
                    return None

                # 2. Handle tag updates if provided
                if new_tag_ids is not None:
                    # Get current tag IDs for usage count updates
                    current_tag_ids = self.get_blog_tag_ids(blog_id)

                    # Replace tag associations
                    self.replace_blog_tags(blog_id, new_tag_ids)

                    # Update tag usage counts
                    if current_tag_ids:
                        self.decrement_tag_usage_counts(current_tag_ids)
                    if new_tag_ids:
                        self.increment_tag_usage_counts(new_tag_ids)

                # 3. Commit transaction
                self.db.commit()

                # 4. Return updated blog with relationships
                return self.get_by_id(blog_id, include_drafts=True, load_relations=True)

        except IntegrityError as e:
            self.db.rollback()
            if "slug" in str(e):
                raise ValueError(f"Slug already exists: {updates.get('slug')}")
            raise e
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_blog(self, blog_id: str) -> bool:
        """
        Delete blog and clean up associations in a transaction.

        Args:
            blog_id: Blog identifier

        Returns:
            bool: True if successfully deleted
        """
        try:
            with self.db.begin():
                # Get blog and current tag IDs
                blog = self.get_by_id(
                    blog_id, include_drafts=True, load_relations=False
                )
                if not blog:
                    return False

                current_tag_ids = self.get_blog_tag_ids(blog_id)

                # Delete blog (cascades will handle blog_tags)
                self.db.delete(blog)

                # Update tag usage counts
                if current_tag_ids:
                    self.decrement_tag_usage_counts(current_tag_ids)

                self.db.commit()
                return True

        except Exception as e:
            self.db.rollback()
            raise e

    async def list_blogs(
        self, filters: BlogFilters, pagination: PaginationParams
    ) -> PaginatedResponse[Blog]:
        """
        List blogs with complex filtering and pagination.

        Args:
            filters: Blog filters (author, tags, search, etc.)
            pagination: Pagination parameters
        """
        # 1. Build a base query without ordering or eager loading for the count.
        count_query = select(Blog)
        count_query = self._apply_filters(count_query, filters)

        # Use select(func.count()) on the filtered base query.
        # This is more efficient than a subquery from the full-blown query.
        total = await self.db.scalar(select(func.count()).select_from(count_query))

        # 2. Build the main query for the paginated results.
        query = select(Blog)

        # 3. Eager load relationships.
        query = query.options(selectinload(Blog.author), selectinload(Blog.tags))

        # 4. Apply filters to the main query.
        query = self._apply_filters(query, filters)

        # 5. Apply default sorting.
        query = query.order_by(desc(Blog.created_at))

        # 6. Apply pagination.
        offset = (pagination.page - 1) * pagination.per_page
        query = query.offset(offset).limit(pagination.per_page)

        # 7. Execute the main query.
        result = await self.db.execute(query)
        blogs = result.scalars().all()

        # 8. Return the paginated response.
        return PaginatedResponse.create(
            items=blogs, total=total, page=pagination.page, per_page=pagination.per_page
        )

    async def increment_view_count(self, blog_id: str) -> None:
        """
        Increment blog view count.
        This should be called asynchronously in production.
        """
        stmt = (
            update(Blog)
            .where(Blog.id == blog_id)
            .values(view_count=Blog.view_count + 1)
        )

        await self.db.execute(stmt)

        await self.db.commit()

    def get_featured_blogs(self, limit: int = 10) -> List[Blog]:
        """Get featured blogs."""
        return (
            self.db.query(Blog)
            .options(joinedload(Blog.author), selectinload(Blog.tags))
            .filter(and_(Blog.is_featured == True, Blog.is_published == True))
            .order_by(desc(Blog.published_at))
            .limit(limit)
            .all()
        )

    def get_popular_blogs(self, limit: int = 10) -> List[Blog]:
        """Get most popular blogs by view count."""
        return (
            self.db.query(Blog)
            .options(joinedload(Blog.author), selectinload(Blog.tags))
            .filter(Blog.is_published == True)
            .order_by(desc(Blog.view_count))
            .limit(limit)
            .all()
        )

    def get_recent_blogs(self, limit: int = 10) -> List[Blog]:
        """Get most recent published blogs."""
        return (
            self.db.query(Blog)
            .options(joinedload(Blog.author), selectinload(Blog.tags))
            .filter(Blog.is_published == True)
            .order_by(desc(Blog.published_at))
            .limit(limit)
            .all()
        )

    def get_blog_stats(self, blog_id: str) -> Dict[str, int]:
        """Get blog statistics (views, likes, comments)."""
        blog = self.get_by_id(blog_id, include_drafts=True, load_relations=False)
        if not blog:
            return {}

        return {
            "view_count": blog.view_count,
            "like_count": blog.like_count,
            "comment_count": blog.comment_count,
        }

    # Private helper methods for tag operations

    def get_blog_tag_ids(self, blog_id: str) -> List[str]:
        """Get tag IDs associated with a blog."""
        result = self.db.execute(
            text("SELECT tag_id FROM blog_tags WHERE blog_id = :blog_id"),
            {"blog_id": blog_id},
        )
        return [row[0] for row in result]

    def get_blog_tags(self, blog_id: str) -> List[Tag]:
        """Get tags associated with a blog."""
        return (
            self.db.query(Tag)
            .join(blog_tags)
            .filter(blog_tags.c.blog_id == blog_id)
            .all()
        )

    async def associate_tags(self, blog_id: str, tag_ids: List[str]) -> None:
        """Associate tags with a blog."""
        if not tag_ids:
            return

        # Insert associations
        associations = [{"blog_id": blog_id, "tag_id": tag_id} for tag_id in tag_ids]

        await self.db.execute(insert(blog_tags), associations)
        # Don't commit - let the calling transaction handle it

    def replace_blog_tags(self, blog_id: str, new_tag_ids: List[str]) -> None:
        """Replace all tag associations for a blog."""
        # Delete existing associations
        self.db.execute(blog_tags.delete().where(blog_tags.c.blog_id == blog_id))

        # Add new associations
        if new_tag_ids:
            self.associate_tags(blog_id, new_tag_ids)

    async def increment_tag_usage_counts(self, tag_ids: List[str]) -> None:
        """Increment usage count for multiple tags."""
        if not tag_ids:
            return

        stmt = (
            update(Tag)
            .where(Tag.id.in_(tag_ids))
            .values(usage_count=Tag.usage_count + 1)
        )

        await self.db.execute(stmt)
        # Don't commit - let the calling transaction handle it

    async def decrement_tag_usage_counts(self, tag_ids: List[str]) -> None:
        """Decrement usage count for multiple tags."""
        if not tag_ids:
            return

        # Use the SQLAlchemy 2.0 update construct
        stmt = (
            update(Tag)
            .where(Tag.id.in_(tag_ids))
            .values(usage_count=func.greatest(Tag.usage_count - 1, 0))
        )
        await self.db.execute(stmt)
        # Don't commit - let the calling transaction handle it

    def _apply_filters(self, query, filters: BlogFilters):
        """Apply filtering logic to query."""
        # Published status filter
        if not filters.include_drafts:
            query = query.filter(Blog.is_published.is_(True))

        # Author filter
        if filters.author_id:
            query = query.filter(Blog.author_id == filters.author_id)

        # # Featured filter
        # if filters.is_featured is not None:
        #     query = query.filter(Blog.is_featured == filters.is_featured)

        # Published filter
        if not filters.is_published:
            query = query.filter(Blog.is_published == filters.is_published)

        # Tag filter
        if filters.tag_names:
            # Join with tags and filter by tag names
            query = query.join(Blog.tags).filter(Tag.name.in_(filters.tag_names))

        # Search filter (title and content)
        if filters.search_query:
            search_term = f"%{filters.search_query.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Blog.title).like(search_term),
                    func.lower(Blog.content).like(search_term),
                    # func.lower(Blog.summary).like(search_term),
                )
            )

        # Draft visibility based on viewer
        if filters.viewer_id and not filters.include_drafts:
            # Show published blogs OR user's own drafts
            query = query.filter(
                or_(
                    Blog.is_published == True,
                    and_(
                        Blog.author_id == filters.viewer_id, Blog.is_published == False
                    ),
                )
            )

        return query
