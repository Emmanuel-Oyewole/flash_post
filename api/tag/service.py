from typing import Optional
from uuid import UUID
from fastapi import status
from ..user.model import User
from ..shared.tag_repo import TagRepository
from ..shared.pagination import PaginatedResponse, PaginationParams
from .schema import TagResponse, TagCreate, TagUpdate
from ..utils.slug_helper import generate_seo_optimized_slug
from ..exceptions.exceptions import (
    TagConstraintError,
    UnauthorizedError,
    TagExistError,
    TagNotFoundError,
)


class TagService:
    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    async def list_tags(
        self,
        search_query: Optional[str] = None,
        sort_by: str = "usage_count",
        order: str = "desc",
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse[TagResponse]:
        """List tags - public endpoint, no auth required."""
        paginated_tags = await self.tag_repo.list_tags(
            search_query, sort_by, order, pagination
        )

        tag_responses = [
            TagResponse.model_validate(tag) for tag in paginated_tags.items
        ]

        return PaginatedResponse.create(
            items=tag_responses,
            total=paginated_tags.total,
            page=pagination.page if pagination else 1,
            per_page=pagination.per_page if pagination else len(tag_responses),
        )

    async def create_tag(self, tag_data: TagCreate, current_user: User) -> TagResponse:
        """Create tag - ADMIN ONLY."""
        self._require_admin(current_user)

        # Check if tag name already exists
        existing_tag = await self.tag_repo.get_by_name(tag_data.name)
        if existing_tag:
            raise TagExistError(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{tag_data.name}' already exists",
            )
        # Generate slug from name
        slug = await self._generate_unique_slug(tag_data.name)

        tag_dict = {
            "name": tag_data.name.strip(),
            "slug": slug,
            "description": (
                tag_data.description.strip() if tag_data.description else None
            ),
            "color": tag_data.color,
            "usage_count": 0,
        }

        # Create tag
        created_tag = await self.tag_repo.create(tag_dict)
        return TagResponse.model_validate(created_tag)

    async def get_tag_by_id(self, tag_id: str) -> TagResponse:
        """Get single tag - public endpoint, no auth required."""
        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found",
            )

        return TagResponse.model_validate(tag)

    async def update_tag(
        self, tag_id: str, tag_data: TagUpdate, current_user: User
    ) -> TagResponse:
        """Update tag - ADMIN ONLY."""
        # Check if user is admin
        self._require_admin(current_user)

        # Check if tag exists
        existing_tag = await self.tag_repo.get_by_id(tag_id)
        if not existing_tag:
            raise TagNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found",
            )

        # Prepare updates
        updates = {}

        if tag_data.name and tag_data.name.strip() != existing_tag.name:
            # Check if new name already exists
            name_exists = await self.tag_repo.get_by_name(tag_data.name)
            if name_exists and name_exists.id != tag_id:
                raise TagExistError(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag with name '{tag_data.name}' already exists",
                )

            updates["name"] = tag_data.name.strip()
            # Generate new slug if name changed
            updates["slug"] = await self._generate_unique_slug(
                tag_data.name, exclude_id=tag_id
            )

        if tag_data.description is not None:
            updates["description"] = (
                tag_data.description.strip() if tag_data.description else None
            )

        if tag_data.color is not None:
            updates["color"] = tag_data.color

        # Update tag
        updated_tag = await self.tag_repo.update(tag_id, updates)
        return TagResponse.model_validate(updated_tag)

    async def delete_tag(self, tag_id: str, current_user: User) -> bool:
        """Delete tag - ADMIN ONLY."""
        # Check if user is admin
        self._require_admin(current_user)

        # Check if tag exists
        existing_tag = await self.tag_repo.get_by_id(tag_id)
        if not existing_tag:
            raise TagNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found",
            )
        # Check if tag is being used by blogs
        if existing_tag.usage_count > 0:
            raise TagConstraintError(status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete tag '{existing_tag.name}' because it's used by {existing_tag.usage_count} blog(s). Please remove it from all blogs first."
            )
        # Delete tag
        return await self.tag_repo.delete(tag_id)

    def _require_admin(self, user: User) -> None:
        """Check if user has admin role."""
        if not user:
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if not user.is_active:
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        if user.role != "admin":
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access required"
            )

    async def _generate_unique_slug(
        self, name: str, exclude_id: Optional[str] = None
    ) -> str:
        """Generate unique slug for tag."""
        from ..utils.slug_helper import generate_seo_optimized_slug

        base_slug = generate_seo_optimized_slug(name)

        # Check if base slug is available
        if not await self.tag_repo.slug_exists(base_slug, exclude_id=exclude_id):
            return base_slug

        # Try with incrementing counter
        for counter in range(1, 101):
            candidate_slug = f"{base_slug}-{counter}"
            if not await self.tag_repo.slug_exists(
                candidate_slug, exclude_id=exclude_id
            ):
                return candidate_slug

        # Fallback to UUID suffix
        import uuid

        return f"{base_slug}-{str(uuid.uuid4())[:8]}"
