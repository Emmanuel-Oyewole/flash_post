from datetime import datetime, timezone
from uuid import UUID
from fastapi import status
from sqlalchemy.exc import IntegrityError
from ..shared.blog_repo import BlogRepository
from ..shared.tag_repo import TagRepository
from ..blogs.schema import BlogCreate
from ..utils.slug_helper import generate_seo_optimized_slug
from ..exceptions.exceptions import UnauthorizedError, TagNotFoundError

from typing import List, Optional
from uuid import uuid4

from ..blogs.schema import BlogCreate, BlogUpdate, BlogResponse, BlogFilters
from ..models import Blog
from ..models import Tag
from ..models import User
from ..shared.blog_repo import BlogRepository
from ..shared.tag_repo import TagRepository
from ..shared.user_repo import UserRepository
from ..shared.pagination import PaginationParams, PaginatedResponse
from ..utils.slug_helper import generate_seo_optimized_slug
from ..config.helpers import logger
from ..exceptions.exceptions import (
    BlogNotFoundError,
    UnauthorizedError,
    ValidationError,
    SlugConflictError,
)


class BlogService:
    """
    Stateless blog service handling all blog-related business logic.
    Depends on repositories for data access and transactions.
    """

    def __init__(
        self,
        blog_repo: BlogRepository,
        tag_repo: TagRepository,
        user_repo: UserRepository,
    ):
        self.blog_repo = blog_repo
        self.tag_repo = tag_repo
        self.user_repo = user_repo

    async def create_blog(self, blog_data: BlogCreate, author_id: str) -> BlogResponse:
        """
        Create a new blog post.

        Args:
            blog_data: Validated blog creation data from Pydantic
            author_id: ID of the blog author (from JWT token)

        Returns:
            BlogResponse: Created blog with all related data

        Raises:
            UnauthorizedError: If author is invalid or inactive
            ValidationError: If tags don't exist or other validation fails
            SlugConflictError: If unable to generate unique slug
        """
        # 1. Validate author exists and is active
        author = await self._validate_author(author_id)

        # 2. Validate and get existing tags (admin-only creation)
        tags = await self._validate_and_get_tags(blog_data.tags)

        # 3. Generate unique slug
        slug = await self._generate_unique_slug(blog_data.title)

        # 4. Generate summary if not provided
        # summary = blog_data.summary or self._generate_summary(blog_data.content)

        # 5. Prepare blog data with processed fields
        blog_dict = {
            # "id": str(uuid4()),
            "title": blog_data.title.strip(),
            "content": blog_data.content.strip(),
            "slug": slug,
            # 'summary': summary,
            "author_id": author.id,
            "is_published": blog_data.is_published,
            # 'is_featured': False,  # Only admins can feature blogs
            "published_at": (
                datetime.now(timezone.utc) if blog_data.is_published else None
            ),
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
        }

        # 6. Create blog with tags in transaction
        created_blog = await self.blog_repo.create_with_tags(
            blog_dict, [tag.id for tag in tags]
        )

        return BlogResponse.model_validate(created_blog)

    async def get_blog_by_id(
        self, blog_id: str, user_id: Optional[str] = None
    ) -> BlogResponse:
        """
        Get blog by ID with permission checks.

        Args:
            blog_id: Blog identifier
            user_id: Current user ID (optional, for draft access)

        Returns:
            BlogResponse: Blog data with related information

        Raises:
            BlogNotFoundError: If blog doesn't exist or user can't access it
        """
        blog = await self.blog_repo.get_by_id(blog_id, include_drafts=True)

        if not blog:
            raise BlogNotFoundError(blog_id)

        # Check access permissions for drafts
        if not blog.is_published and blog.author_id != user_id:
            raise BlogNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"blog with blog id: {blog_id} does not exist",
            )

        # Increment view count for published blogs (async in real implementation)
        if blog.is_published:
            await self.blog_repo.increment_view_count(blog_id)

            await self.blog_repo.db.refresh(blog)

        return BlogResponse.model_validate(blog)

    async def get_blog_by_slug(
        self, slug: str, user_id: Optional[str] = None
    ) -> BlogResponse:
        """
        Get blog by slug with permission checks.

        Args:
            slug: Blog slug
            user_id: Current user ID (optional, for draft access)

        Returns:
            BlogResponse: Blog data with related information

        Raises:
            BlogNotFoundError: If blog doesn't exist or user can't access it
        """
        blog = await self.blog_repo.get_by_slug(slug, include_drafts=True)
        print(blog)

        if not blog:
            raise BlogNotFoundError(f"Blog with slug '{slug}' not found")

        # Check access permissions for drafts
        print(blog.author_id == user_id)
        if not blog.is_published and blog.author_id != user_id:
            raise BlogNotFoundError(f"Blog with slug '{slug}' not found")

        # Increment view count for published blogs
        if blog.is_published:

            await self.blog_repo.increment_view_count(blog.id)

            await self.blog_repo.db.refresh(blog)

        return BlogResponse.model_validate(blog)

    async def update_blog(
        self, blog_id: str, updates: BlogUpdate, user_id: str
    ) -> BlogResponse:
        """
        Update existing blog post.

        Args:
            blog_id: Blog identifier
            updates: Validated update data from Pydantic
            user_id: Current user ID (must be author)

        Returns:
            BlogResponse: Updated blog with all related data

        Raises:
            BlogNotFoundError: If blog doesn't exist
            UnauthorizedError: If user is not the author
            ValidationError: If tags don't exist or other validation fails
        """
        # 1. Get existing blog with permission check
        blog = await self.blog_repo.get_by_id(blog_id, include_drafts=True)
        if not blog:
            raise BlogNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blog {blog_id} not found",
            )

        if blog.author_id != user_id:
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only the author can update this blog",
            )

        # 2. Validate and get new tags if provided
        new_tag_ids = None
        if updates.tags is not None:
            new_tags = await self._validate_and_get_tags(updates.tags)
            new_tag_ids = [tag.id for tag in new_tags]

        # 3. Generate new slug if title changed
        new_slug = blog.slug
        if updates.title and updates.title.strip() != blog.title:
            new_slug = await self._generate_unique_slug(
                updates.title, exclude_blog_id=blog_id
            )

        # 4. Handle publish state changes
        published_at = blog.published_at
        if updates.is_published is not None:
            if updates.is_published and not blog.is_published:
                # Publishing draft
                published_at = datetime.now(timezone.utc)
            elif not updates.is_published and blog.is_published:
                # Unpublishing (back to draft)
                published_at = None

        # 5. Build update dictionary with only changed fields
        update_dict = {}

        if updates.title and updates.title.strip() != blog.title:
            update_dict["title"] = updates.title.strip()

        if updates.content and updates.content.strip() != blog.content:
            update_dict["content"] = updates.content.strip()
            # # Regenerate summary if content changed and no new summary provided
            # if not updates.summary:
            #     update_dict["summary"] = self._generate_summary(updates.content)

        # if updates.summary and updates.summary.strip() != blog.summary:
        #     update_dict["summary"] = updates.summary.strip()

        if new_slug != blog.slug:
            update_dict["slug"] = new_slug

        if (
            updates.is_published is not None
            and updates.is_published != blog.is_published
        ):
            update_dict["is_published"] = updates.is_published
            update_dict["published_at"] = published_at

        # 6. Update blog with tags in transaction
        updated_blog = await self.blog_repo.update_with_tags(
            blog_id, update_dict, new_tag_ids
        )

        return BlogResponse.model_validate(updated_blog)

    async def delete_blog(self, blog_id: str, user_id: str) -> bool:
        """
        Delete blog post.

        Args:
            blog_id: Blog identifier
            user_id: Current user ID (must be author)

        Returns:
            bool: True if successfully deleted

        Raises:
            BlogNotFoundError: If blog doesn't exist
            UnauthorizedError: If user is not the author
        """
        # 1. Get existing blog with permission check
        blog = await self.blog_repo.get_by_id(blog_id, include_drafts=True)
        if not blog:
            raise BlogNotFoundError(f"Blog {blog_id} not found")

        if blog.author_id != user_id:
            raise UnauthorizedError("Only the author can delete this blog")

        # 2. Delete blog (repository handles tag associations cleanup)
        return await self.blog_repo.delete_blog(blog_id)

    async def list_blogs(
        self,
        filters: BlogFilters,
        pagination: PaginationParams,
        user_id: Optional[str] = None,
    ) -> PaginatedResponse[BlogResponse]:
        """
        List blogs with filtering and pagination.

        Args:
            filters: Blog filters (author, tags, published status, etc.)
            pagination: Pagination parameters
            user_id: Current user ID (for draft visibility)

        Returns:
            PaginatedResponse[BlogResponse]: Paginated list of blogs
        """
        # Add user context to filters for draft visibility
        if user_id:
            filters.viewer_id = user_id

        # Get paginated blogs from repository
        paginated_blogs = await self.blog_repo.list_blogs(filters, pagination)
        logger.debug(f"perginated response:{paginated_blogs}")

        # Convert to response schema
        blog_responses = [
            BlogResponse.model_validate(blog) for blog in paginated_blogs.items
        ]

        return PaginatedResponse(
            items=blog_responses,
            total=paginated_blogs.total,
            page=paginated_blogs.page,
            per_page=paginated_blogs.per_page,
            total_pages=paginated_blogs.total_pages,
            has_next=paginated_blogs.has_next,
            has_prev=paginated_blogs.has_prev,
        )

    def list_user_blogs(
        self,
        author_id: str,
        pagination: PaginationParams,
        user_id: Optional[str] = None,
        include_drafts: bool = False,
    ) -> PaginatedResponse[BlogResponse]:
        """
        List blogs by specific author.

        Args:
            author_id: Author's user ID
            pagination: Pagination parameters
            user_id: Current user ID (for draft visibility)
            include_drafts: Whether to include drafts (only if user is author)

        Returns:
            PaginatedResponse[BlogResponse]: Paginated list of author's blogs
        """
        # Only author can see their own drafts
        if include_drafts and author_id != user_id:
            include_drafts = False

        filters = BlogFilters(
            author_id=author_id, include_drafts=include_drafts, viewer_id=user_id
        )

        return self.list_blogs(filters, pagination, user_id)

    async def publish_blog(self, blog_id: str, user_id: str) -> BlogResponse:
        """
        Publish a draft blog.

        Args:
            blog_id: Blog identifier
            user_id: Current user ID (must be author)

        Returns:
            BlogResponse: Published blog

        Raises:
            BlogNotFoundError: If blog doesn't exist
            UnauthorizedError: If user is not the author
            ValidationError: If blog is already published
        """
        blog = await self.blog_repo.get_by_id(blog_id, include_drafts=True)
        if not blog:
            raise BlogNotFoundError(f"Blog {blog_id} not found")

        if blog.author_id != user_id:
            raise UnauthorizedError("Only the author can publish this blog")

        if blog.is_published:
            raise ValidationError("Blog is already published")

        # Update to published status
        update_dict = {"is_published": True, "published_at": datetime.now(timezone.utc)}

        updated_blog = await self.blog_repo.update_blog(blog_id, update_dict)

        return BlogResponse.model_validate(updated_blog)

    async def unpublish_blog(self, blog_id: str, user_id: str) -> BlogResponse:
        """
        Unpublish a blog (convert back to draft).

        Args:
            blog_id: Blog identifier
            user_id: Current user ID (must be author)

        Returns:
            BlogResponse: Unpublished blog

        Raises:
            BlogNotFoundError: If blog doesn't exist
            UnauthorizedError: If user is not the author
            ValidationError: If blog is already a draft
        """
        blog = await self.blog_repo.get_by_id(blog_id, include_drafts=True)
        if not blog:
            raise BlogNotFoundError(f"Blog {blog_id} not found")

        if blog.author_id != user_id:
            raise UnauthorizedError("Only the author can unpublish this blog")

        if not blog.is_published:
            raise ValidationError("Blog is already a draft")

        # Update to draft status
        update_dict = {"is_published": False, "published_at": None}

        updated_blog = await self.blog_repo.update_blog(blog_id, update_dict)

        return BlogResponse.model_validate(updated_blog)

    # Private helper methods

    async def _validate_author(self, author_id: str) -> User:
        """
        Validate that author exists and is active.

        Raises:
            UnauthorizedError: If author is invalid or inactive
        """
        author = await self.user_repo.get_user_by_id(author_id)
        if not author:
            raise UnauthorizedError("Invalid author")

        if not author.is_active:
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Author account is inactive",
            )

        # if not author.email_verified:
        #     raise UnauthorizedError(status_code=status.HTTP_401_UNAUTHORIZED,detail="Only verified account can create blog")

        return author

    async def _validate_and_get_tags(self, tag_names: List[str]) -> List[Tag]:
        """
        Validate that all requested tags exist (admin-only creation).

        Args:
            tag_names: List of tag names to validate

        Returns:
            List[Tag]: List of existing tag objects

        Raises:
            ValidationError: If any tags don't exist
        """
        if not tag_names:
            return []

        # Remove duplicates and normalize
        unique_names = list(
            set(name.strip().lower() for name in tag_names if name.strip())
        )

        if not unique_names:
            return []

        # Get existing tags
        existing_tags = await self.tag_repo.get_by_names(unique_names)
        existing_names = {tag.name.lower() for tag in existing_tags}

        # Check for missing tags
        missing_tags = set(unique_names) - existing_names
        if missing_tags:
            raise TagNotFoundError(
                status.HTTP_404_NOT_FOUND,
                detail=f"The following tags do not exist: {', '.join(missing_tags)}. "
                "Please contact an administrator to create new tags.",
            )

        return existing_tags

    async def _generate_unique_slug(
        self, title: str, exclude_blog_id: Optional[str] = None
    ) -> str:
        """
        Generate globally unique slug from title.

        Args:
            title: Blog title
            exclude_blog_id: Blog ID to exclude from uniqueness check (for updates)

        Returns:
            str: Unique slug

        Raises:
            SlugConflictError: If unable to generate unique slug after many attempts
        """
        base_slug = generate_seo_optimized_slug(title)

        # Check if base slug is available
        if not await self.blog_repo.slug_exists(base_slug, exclude_id=exclude_blog_id):
            return base_slug

        # Try with incrementing counter
        for counter in range(1, 101):  # Try up to 100 variations
            candidate_slug = f"{base_slug}-{counter}"
            if not await self.blog_repo.slug_exists(
                candidate_slug, exclude_id=exclude_blog_id
            ):
                return candidate_slug

        # Fallback to UUID suffix if too many conflicts
        import uuid

        fallback_slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"

        # Final check (should be unique, but just in case)
        if not await self.blog_repo.slug_exists(
            fallback_slug, exclude_id=exclude_blog_id
        ):
            return fallback_slug

        raise SlugConflictError(f"Unable to generate unique slug for title: {title}")

    # def _generate_summary(self, content: str, max_length: int = 200) -> str:
    #     """
    #     Generate summary from content.

    #     Args:
    #         content: Blog content (plain text)
    #         max_length: Maximum summary length

    #     Returns:
    #         str: Generated summary
    #     """
    #     cleaned_content = content.strip()

    #     if not cleaned_content:
    #         return ""

    #     if len(cleaned_content) <= max_length:
    #         return cleaned_content

    #     # Try to find a good breaking point (sentence endings)
    #     truncated = cleaned_content[:max_length]
    #     sentence_ends = [
    #         truncated.rfind("."),
    #         truncated.rfind("!"),
    #         truncated.rfind("?"),
    #     ]

    #     best_end = max(sentence_ends)

    #     # If we found a sentence ending in the latter 70% of the limit, use it
    #     if best_end > max_length * 0.7:
    #         return cleaned_content[: best_end + 1]

    #     # Otherwise, truncate at word boundary
    #     last_space = truncated.rfind(" ")
    #     if last_space > max_length * 0.8:
    #         return cleaned_content[:last_space] + "..."

    #     # Fallback: hard truncate with ellipsis
    #     return cleaned_content[: max_length - 3].rstrip() + "..."
