"""
Advanced pytest configuration and fixtures.

This file demonstrates:
- Custom pytest markers
- Advanced fixtures
- Test configuration
- Performance testing
- Database setup/teardown
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from ...src.config.database import Base, get_db
from ...src.main import app
from ..factories.user import UserFactory


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "blog: mark test as blog related")
    config.addinivalue_line("markers", "performance: mark test as performance test")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for fast tests
    # Or use PostgreSQL test database for production-like testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,  # Set to True for SQL debugging
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any changes


@pytest.fixture
async def override_get_db(db_session):
    """Override the database dependency."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_user(db_session: AsyncSession) -> dict:
    """Create an authenticated user and return user data with tokens."""
    from ...src.utils.auth import create_access_token, create_refresh_token

    # Create user
    password = "testpassword123"
    user = UserFactory.create(password=password)
    await db_session.commit()

    # Generate tokens
    token_data = {"sub": user.email, "user_id": str(user.id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "password": password,
    }


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> dict:
    """Create an authenticated admin user."""
    from ...src.models.user_model import UserRole
    from ...src.utils.auth import create_access_token

    user = UserFactory.create(role=UserRole.ADMIN)
    await db_session.commit()

    token_data = {"sub": user.email, "user_id": str(user.id)}
    access_token = create_access_token(data=token_data)

    return {"user": user, "access_token": access_token}


@pytest.fixture
async def multiple_users(db_session: AsyncSession) -> list:
    """Create multiple test users."""
    users = UserFactory.create_batch(5)
    await db_session.commit()
    return users


@pytest.fixture
async def blogs_with_users(db_session: AsyncSession) -> dict:
    """Create blogs with their associated users."""
    from ..factories.blog import BlogFactory

    users = UserFactory.create_batch(3)
    blogs = []

    for user in users:
        user_blogs = BlogFactory.create_batch(2, author=user)
        blogs.extend(user_blogs)

    await db_session.commit()

    return {"users": users, "blogs": blogs}


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    from unittest.mock import AsyncMock, Mock

    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)

    return mock_redis


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    from unittest.mock import AsyncMock, Mock

    mock_service = Mock()
    mock_service.send_email = AsyncMock(return_value=True)
    mock_service.send_verification_email = AsyncMock(return_value=True)
    mock_service.send_password_reset_email = AsyncMock(return_value=True)

    return mock_service


# Data fixtures
@pytest.fixture
def sample_blog_data():
    """Sample blog data for testing."""
    return {
        "title": "Sample Blog Title",
        "content": "This is a sample blog content for testing purposes. " * 10,
        "is_published": True,
        "tags": ["python", "testing", "fastapi"],
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "bio": "Test user biography",
    }


# Database seeding fixtures
@pytest.fixture
async def seed_database(db_session: AsyncSession):
    """Seed database with test data."""
    from ..factories.blog import BlogFactory

    # Create users
    users = UserFactory.create_batch(10)

    # Create blogs
    blogs = []
    for user in users:
        user_blogs = BlogFactory.create_batch(3, author=user, is_published=True)
        blogs.extend(user_blogs)

    await db_session.commit()

    return {
        "users": users,
        "blogs": blogs,
        "total_users": len(users),
        "total_blogs": len(blogs),
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup code here if needed
    # This runs after each test


# Configuration fixtures
@pytest.fixture
def test_settings():
    """Test-specific settings."""
    return {
        "database_url": "sqlite+aiosqlite:///:memory:",
        "secret_key": "test-secret-key",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7,
    }


# HTTP client fixtures with different configurations
@pytest.fixture
async def unauthorized_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_client(
    override_get_db, admin_user
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with admin authentication."""
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {admin_user['access_token']}"},
    ) as ac:
        yield ac


@pytest.fixture
async def user_client(
    override_get_db, authenticated_user
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with regular user authentication."""
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    ) as ac:
        yield ac
