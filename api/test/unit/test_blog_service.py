"""
Unit tests for blog service functions.

This demonstrates:
- Testing business logic
- Mocking dependencies
- Testing edge cases
- Service layer testing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from ...src.blogs.service import BlogService
from ...src.models.blog_model import Blog
from ...src.models.user_model import User
from ..factories.blog import BlogFactory
from ..factories.user import UserFactory


class TestBlogService:
    """Unit tests for BlogService class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=AsyncSession)

    @pytest.fixture
    def blog_service(self, mock_db_session):
        """Create BlogService instance with mocked dependencies."""
        return BlogService(db=mock_db_session)

    async def test_create_blog_success(self, blog_service, mock_db_session):
        """Test successful blog creation."""
        # Arrange
        user = UserFactory.build()
        blog_data = {
            "title": "Test Blog",
            "content": "Test content",
            "is_published": True,
        }

        # Mock database operations
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Act
        result = await blog_service.create_blog(user_id=user.id, blog_data=blog_data)

        # Assert
        assert result.title == blog_data["title"]
        assert result.content == blog_data["content"]
        assert result.author_id == user.id
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_get_blog_by_id_success(self, blog_service, mock_db_session):
        """Test retrieving blog by ID."""
        # Arrange
        blog = BlogFactory.build()
        mock_db_session.get = AsyncMock(return_value=blog)

        # Act
        result = await blog_service.get_blog_by_id(blog.id)

        # Assert
        assert result == blog
        mock_db_session.get.assert_called_once_with(Blog, blog.id)

    async def test_get_blog_by_id_not_found(self, blog_service, mock_db_session):
        """Test retrieving non-existent blog."""
        # Arrange
        blog_id = "non-existent-id"
        mock_db_session.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError, match="Blog not found"):
            await blog_service.get_blog_by_id(blog_id)

    async def test_update_blog_success(self, blog_service, mock_db_session):
        """Test successful blog update."""
        # Arrange
        blog = BlogFactory.build()
        update_data = {"title": "Updated Title", "content": "Updated content"}

        mock_db_session.get = AsyncMock(return_value=blog)
        mock_db_session.commit = AsyncMock()

        # Act
        result = await blog_service.update_blog(blog.id, update_data)

        # Assert
        assert result.title == update_data["title"]
        assert result.content == update_data["content"]
        mock_db_session.commit.assert_called_once()

    async def test_delete_blog_success(self, blog_service, mock_db_session):
        """Test successful blog deletion."""
        # Arrange
        blog = BlogFactory.build()
        mock_db_session.get = AsyncMock(return_value=blog)
        mock_db_session.delete = Mock()
        mock_db_session.commit = AsyncMock()

        # Act
        await blog_service.delete_blog(blog.id)

        # Assert
        mock_db_session.delete.assert_called_once_with(blog)
        mock_db_session.commit.assert_called_once()

    async def test_search_blogs_with_query(self, blog_service, mock_db_session):
        """Test blog search functionality."""
        # Arrange
        search_query = "Python"
        mock_blogs = [BlogFactory.build() for _ in range(3)]

        with patch.object(blog_service, "_build_search_query") as mock_search:
            mock_search.return_value.offset.return_value.limit.return_value.all = (
                AsyncMock(return_value=mock_blogs)
            )

            # Act
            result = await blog_service.search_blogs(
                query=search_query, page=1, limit=10
            )

            # Assert
            assert len(result) == 3
            mock_search.assert_called_once()

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"title": ""},  # Empty title
            {"title": "Valid", "content": ""},  # Empty content
            {"title": "a" * 300},  # Title too long
        ],
    )
    async def test_create_blog_validation_error(
        self, blog_service, mock_db_session, invalid_data
    ):
        """Test blog creation with invalid data."""
        user = UserFactory.build()

        with pytest.raises(ValueError):
            await blog_service.create_blog(user_id=user.id, blog_data=invalid_data)

    async def test_increment_view_count(self, blog_service, mock_db_session):
        """Test incrementing blog view count."""
        # Arrange
        blog = BlogFactory.build(view_count=5)
        mock_db_session.get = AsyncMock(return_value=blog)
        mock_db_session.commit = AsyncMock()

        # Act
        await blog_service.increment_view_count(blog.id)

        # Assert
        assert blog.view_count == 6
        mock_db_session.commit.assert_called_once()

    async def test_get_user_blogs(self, blog_service, mock_db_session):
        """Test retrieving blogs by user."""
        # Arrange
        user = UserFactory.build()
        user_blogs = [BlogFactory.build(author_id=user.id) for _ in range(3)]

        with patch.object(blog_service, "_get_user_blogs_query") as mock_query:
            mock_query.return_value.all = AsyncMock(return_value=user_blogs)

            # Act
            result = await blog_service.get_user_blogs(user.id)

            # Assert
            assert len(result) == 3
            assert all(blog.author_id == user.id for blog in result)

    async def test_publish_blog(self, blog_service, mock_db_session):
        """Test publishing a blog."""
        # Arrange
        blog = BlogFactory.build(is_published=False, published_at=None)
        mock_db_session.get = AsyncMock(return_value=blog)
        mock_db_session.commit = AsyncMock()

        # Act
        await blog_service.publish_blog(blog.id)

        # Assert
        assert blog.is_published is True
        assert blog.published_at is not None
        mock_db_session.commit.assert_called_once()

    async def test_unpublish_blog(self, blog_service, mock_db_session):
        """Test unpublishing a blog."""
        # Arrange
        from datetime import datetime, timezone

        blog = BlogFactory.build(
            is_published=True, published_at=datetime.now(timezone.utc)
        )
        mock_db_session.get = AsyncMock(return_value=blog)
        mock_db_session.commit = AsyncMock()

        # Act
        await blog_service.unpublish_blog(blog.id)

        # Assert
        assert blog.is_published is False
        assert blog.published_at is None
        mock_db_session.commit.assert_called_once()


class TestBlogServiceHelpers:
    """Test helper functions in BlogService."""

    def test_generate_slug(self):
        """Test slug generation from title."""
        from ...src.blogs.service import BlogService

        test_cases = [
            ("Hello World", "hello-world"),
            ("Python Programming Tutorial!", "python-programming-tutorial"),
            ("Special Characters @#$%", "special-characters"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("UPPERCASE TITLE", "uppercase-title"),
        ]

        for title, expected_slug in test_cases:
            result = BlogService._generate_slug(title)
            assert result == expected_slug

    def test_validate_blog_data(self):
        """Test blog data validation."""
        from ...src.blogs.service import BlogService

        # Valid data
        valid_data = {
            "title": "Valid Title",
            "content": "Valid content with enough length",
            "is_published": True,
        }

        assert BlogService._validate_blog_data(valid_data) is True

        # Invalid data
        invalid_cases = [
            {"title": ""},  # Empty title
            {"title": "Valid", "content": ""},  # Empty content
            {"title": "a" * 300, "content": "Valid"},  # Title too long
        ]

        for invalid_data in invalid_cases:
            with pytest.raises(ValueError):
                BlogService._validate_blog_data(invalid_data)


class TestBlogServiceIntegration:
    """Integration tests with real database session."""

    async def test_full_blog_lifecycle(self, db_session: AsyncSession):
        """Test complete blog lifecycle: create, read, update, delete."""
        from ...src.blogs.service import BlogService

        service = BlogService(db=db_session)
        user = UserFactory.create()
        await db_session.commit()

        # Create blog
        blog_data = {
            "title": "Integration Test Blog",
            "content": "This is a test blog for integration testing",
            "is_published": False,
        }

        created_blog = await service.create_blog(user.id, blog_data)
        assert created_blog.id is not None

        # Read blog
        retrieved_blog = await service.get_blog_by_id(created_blog.id)
        assert retrieved_blog.title == blog_data["title"]

        # Update blog
        update_data = {"title": "Updated Integration Test Blog"}
        updated_blog = await service.update_blog(created_blog.id, update_data)
        assert updated_blog.title == update_data["title"]

        # Publish blog
        await service.publish_blog(created_blog.id)
        published_blog = await service.get_blog_by_id(created_blog.id)
        assert published_blog.is_published is True

        # Delete blog
        await service.delete_blog(created_blog.id)

        with pytest.raises(ValueError):
            await service.get_blog_by_id(created_blog.id)

    async def test_concurrent_blog_creation(self, db_session: AsyncSession):
        """Test creating multiple blogs concurrently."""
        import asyncio
        from ...src.blogs.service import BlogService

        service = BlogService(db=db_session)
        user = UserFactory.create()
        await db_session.commit()

        async def create_blog(index):
            blog_data = {
                "title": f"Concurrent Blog {index}",
                "content": f"Content for blog {index}",
                "is_published": True,
            }
            return await service.create_blog(user.id, blog_data)

        # Create 5 blogs concurrently
        tasks = [create_blog(i) for i in range(5)]
        blogs = await asyncio.gather(*tasks)

        assert len(blogs) == 5
        assert all(blog.author_id == user.id for blog in blogs)

        # Verify all blogs have unique IDs
        blog_ids = [blog.id for blog in blogs]
        assert len(set(blog_ids)) == 5
