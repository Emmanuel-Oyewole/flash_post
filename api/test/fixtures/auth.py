import pytest

from ...src.config.settings import settings
from ...src.utils.auth import create_jwt_token


@pytest.fixture
async def auth_headers(created_test_user):
    """Create authorization headers with JWT token."""
    token = create_jwt_token(
        data={"sub": str(created_test_user.id)},
        secret_key=settings.access_token_secret_key,
        expires_delta=settings.access_token_expires_minute,
        is_refresh_token=False,
    )
    return {"Authorization": f"Bearer {token}"}


# @pytest.fixture
# async def admin_auth_headers(created_admin_user):
#     """Create admin authorization headers with JWT token."""
#     token = create_access_token(data={"sub": str(created_admin_user.id)})
#     return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def expired_auth_headers():
    """Create expired authorization headers for testing."""
    # Create token with negative expiry
    token = create_jwt_token(
        data={"sub": "test-user-id"},
        secret_key=settings.access_token_secret_key,
        expires_delta=settings.access_token_expires_minute,
        is_refresh_token=False,
        expires_delta=-1,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def invalid_auth_headers():
    """Create invalid authorization headers for testing."""
    return {"Authorization": "Bearer invalid-token"}

#####################################################


@pytest.fixture
async def override_get_current_user(created_test_user):
    """Override the get_current_user dependency."""
    from ...src.main import app
    from ...src.dependencies.auth_dep import get_current_user

    async def _override_get_current_user():
        return created_test_user

    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def override_get_current_user_another(another_test_user):
    """Override get_current_user with another user for permission tests."""
    from ...src.main import app
    from ...src.dependencies.auth_dep import get_current_user

    async def _override_get_current_user():
        return another_test_user

    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def override_get_current_user_none():
    """Override get_current_user to return None for unauthorized tests."""
    from ...src.main import app
    from ...src.dependencies.auth_dep import get_current_user
    from fastapi import HTTPException, status

    async def _override_get_current_user():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()
