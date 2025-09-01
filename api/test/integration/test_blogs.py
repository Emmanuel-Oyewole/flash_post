"""
Integration tests for Blog endpoints.

This file demonstrates various testing patterns:
- Unit tests for individual functions
- Integration tests for API endpoints
- Authentication testing
- Error handling
- Database interactions
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from ...src.models.blog_model import Blog
from ...src.models.user_model import User
from ..factories.blog import BlogFactory
from ..factories.user import UserFactory


class TestBlogEndpoints:
    """Test class for blog-related endpoints."""

    async def test_create_blog_success(
        self, client: AsyncClient, authenticated_user: dict, db_session: AsyncSession
    ):
        """Test successful blog creation."""
        blog_data = {
            "title": "My Test Blog",
            "content": "This is a test blog content",
            "is_published": True,
        }

        response = await client.post(
            "/blogs/",
            json=blog_data,
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == blog_data["title"]
        assert data["content"] == blog_data["content"]
        assert data["is_published"] == blog_data["is_published"]
        assert "slug" in data
        assert data["author_id"] == str(authenticated_user["user"]["id"])

    async def test_create_blog_unauthorized(self, client: AsyncClient):
        """Test blog creation without authentication."""
        blog_data = {"title": "My Test Blog", "content": "This is a test blog content"}

        response = await client.post("/blogs/", json=blog_data)

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_get_all_blogs(self, client: AsyncClient, db_session: AsyncSession):
        """Test retrieving all blogs."""
        # Create test blogs using factory
        user = UserFactory.create()
        blogs = BlogFactory.create_batch(3, author=user, is_published=True)
        await db_session.commit()

        response = await client.get("/blogs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["blogs"]) >= 3
        assert "total" in data
        assert "page" in data

    async def test_get_blog_by_id(self, client: AsyncClient, db_session: AsyncSession):
        """Test retrieving a specific blog by ID."""
        user = UserFactory.create()
        blog = BlogFactory.create(author=user, is_published=True)
        await db_session.commit()

        response = await client.get(f"/blogs/{blog.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(blog.id)
        assert data["title"] == blog.title

    async def test_get_nonexistent_blog(self, client: AsyncClient):
        """Test retrieving a blog that doesn't exist."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"

        response = await client.get(f"/blogs/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_blog_success(
        self, client: AsyncClient, authenticated_user: dict, db_session: AsyncSession
    ):
        """Test successful blog update by owner."""
        # Create blog owned by authenticated user
        blog = BlogFactory.create(author_id=authenticated_user["user"]["id"])
        await db_session.commit()

        update_data = {"title": "Updated Title", "content": "Updated content"}

        response = await client.put(
            f"/blogs/{blog.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]

    async def test_update_blog_unauthorized(
        self, client: AsyncClient, authenticated_user: dict, db_session: AsyncSession
    ):
        """Test updating a blog owned by another user."""
        # Create blog owned by different user
        other_user = UserFactory.create()
        blog = BlogFactory.create(author=other_user)
        await db_session.commit()

        update_data = {"title": "Hacked Title"}

        response = await client.put(
            f"/blogs/{blog.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 403

    async def test_delete_blog_success(
        self, client: AsyncClient, authenticated_user: dict, db_session: AsyncSession
    ):
        """Test successful blog deletion by owner."""
        blog = BlogFactory.create(author_id=authenticated_user["user"]["id"])
        await db_session.commit()

        response = await client.delete(
            f"/blogs/{blog.id}",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 204

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"title": ""},  # Empty title
            {"title": "Valid", "content": ""},  # Empty content
            {"content": "Valid content"},  # Missing title
            {"title": "a" * 300, "content": "Valid content"},  # Title too long
        ],
    )
    async def test_create_blog_validation_errors(
        self, client: AsyncClient, authenticated_user: dict, invalid_data: dict
    ):
        """Test blog creation with invalid data."""
        response = await client.post(
            "/blogs/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 422  # Validation error


class TestBlogModel:
    """Unit tests for the Blog model."""

    async def test_blog_model_creation(self, db_session: AsyncSession):
        """Test creating a blog model instance."""
        user = UserFactory.create()
        blog = BlogFactory.create(author=user)

        assert blog.title is not None
        assert blog.content is not None
        assert blog.slug is not None
        assert blog.author_id == user.id
        assert isinstance(blog.view_count, int)
        assert isinstance(blog.like_count, int)
        assert isinstance(blog.comment_count, int)

    async def test_blog_slug_generation(self, db_session: AsyncSession):
        """Test that blog slug is generated correctly."""
        user = UserFactory.create()
        blog = BlogFactory.create(author=user, title="This Is A Test Title")

        expected_slug = "this-is-a-test-title"
        assert blog.slug == expected_slug

    async def test_blog_relationships(self, db_session: AsyncSession):
        """Test blog model relationships."""
        user = UserFactory.create()
        blog = BlogFactory.create(author=user)

        # Test author relationship
        assert blog.author.id == user.id
        assert blog in user.blogs


class TestBlogService:
    """Unit tests for blog service functions."""

    async def test_blog_search_functionality(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test blog search functionality."""
        user = UserFactory.create()

        # Create blogs with specific titles
        blog1 = BlogFactory.create(
            author=user, title="Python Programming Tutorial", is_published=True
        )
        blog2 = BlogFactory.create(
            author=user, title="JavaScript for Beginners", is_published=True
        )
        blog3 = BlogFactory.create(
            author=user, title="Advanced Python Concepts", is_published=True
        )
        await db_session.commit()

        # Search for Python blogs
        response = await client.get("/blogs/?search=Python")

        assert response.status_code == 200
        data = response.json()

        # Should return blogs containing "Python"
        python_blogs = [blog for blog in data["blogs"] if "Python" in blog["title"]]
        assert len(python_blogs) >= 2

    async def test_blog_pagination(self, client: AsyncClient, db_session: AsyncSession):
        """Test blog pagination."""
        user = UserFactory.create()
        # Create 15 blogs
        BlogFactory.create_batch(15, author=user, is_published=True)
        await db_session.commit()

        # Test first page
        response = await client.get("/blogs/?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["blogs"]) == 5
        assert data["page"] == 1

        # Test second page
        response = await client.get("/blogs/?page=2&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["blogs"]) == 5
        assert data["page"] == 2


@pytest.mark.asyncio
async def test_blog_performance(client: AsyncClient, db_session: AsyncSession):
    """Test blog endpoint performance."""
    import time

    user = UserFactory.create()
    BlogFactory.create_batch(100, author=user, is_published=True)
    await db_session.commit()

    start_time = time.time()
    response = await client.get("/blogs/")
    end_time = time.time()

    assert response.status_code == 200
    # Should complete within 2 seconds
    assert (end_time - start_time) < 2.0
