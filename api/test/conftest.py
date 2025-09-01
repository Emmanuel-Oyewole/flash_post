import asyncio
import pytest
from httpx import AsyncClient

# Import all fixtures from fixtures directory
from .fixtures.database import *
from .fixtures.user import *
from .fixtures.auth import *
from .fixtures.data import *


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.

    This fixture is crucial for async testing because:
    - It creates a single event loop for the entire test session
    - Prevents "RuntimeError: There is no current event loop" errors
    - Ensures all async tests run in the same event loop
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def client(override_get_db, override_user_service):
    """
    Create test client with overridden dependencies.

    This fixture:
    - Creates an HTTP client for testing API endpoints
    - Automatically applies dependency overrides
    - Ensures clean state between tests
    """
    from ..src.main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
