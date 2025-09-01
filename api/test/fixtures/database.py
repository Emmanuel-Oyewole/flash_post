import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from unittest.mock import AsyncMock

from ...src.config.database import Base, DatabaseSessionManager, get_db_session
# from ...src.config.settings import settings

# Test database URL
TEST_DATABASE_URL = (
    "postgresql+asyncpg://test_user:test_password@localhost/test_flash_post"
)


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_sessionmanager(test_engine):
    """Create a test database session manager."""
    sessionmanager = DatabaseSessionManager(TEST_DATABASE_URL, {"echo": settings.debug})
    yield sessionmanager
    await sessionmanager.close()


@pytest.fixture
async def db_session(test_sessionmanager):
    """Create a test database session with transaction rollback."""
    async with test_sessionmanager.session() as session:
        # Start a transaction
        transaction = await session.begin()
        try:
            yield session
        finally:
            # Always rollback to keep tests isolated
            await transaction.rollback()


@pytest.fixture
async def override_get_db(db_session):
    """Override the get_db_session dependency."""
    from ...src.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()
