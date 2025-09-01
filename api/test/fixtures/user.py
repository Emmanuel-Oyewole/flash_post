import pytest
from ...src.user.schema import CreateUser
from ...src.models import User


@pytest.fixture
async def user_repository(db_session):
    """Create UserRepository instance with test session."""
    from ...src.shared.user_repo import UserRepository

    return UserRepository(db_session)


@pytest.fixture
async def user_service(user_repository):
    """Create UserService instance with test repository."""
    from ...src.user.service import UserService

    return UserService(user_repository)


@pytest.fixture
async def test_user_data():
    """Sample user data for testing."""
    return CreateUser(
        email="test@example.com", password="securepassword123", role="user"
    )


@pytest.fixture
async def override_user_service(user_service):
    """Override the get_user_service dependency."""
    from ...src.main import app
    from ...src.dependencies.auth_dep import get_user_service

    def _override_user_service():
        return user_service

    app.dependency_overrides[get_user_service] = _override_user_service
    yield
    app.dependency_overrides.clear()



# @pytest.fixture
# async def admin_user_data():
#     """Sample admin user data for testing."""
#     return CreateUser(
#         email="admin@example.com", password="securepassword123", role="admin"
#     )


# @pytest.fixture
# async def created_test_user(user_service, test_user_data):
#     """Create a test user in the database."""
#     user = await user_service.register_user(test_user_data)
#     return user


# @pytest.fixture
# async def created_admin_user(user_service, admin_user_data):
#     """Create an admin user in the database."""
#     user = await user_service.register_user(admin_user_data)
#     return user


# @pytest.fixture
# async def multiple_test_users(user_service):
#     """Create multiple test users."""
#     users = []
#     for i in range(3):
#         user_data = CreateUser(
#             email=f"user{i}@example.com", password="securepassword123", role="user"
#         )
#         user = await user_service.register_user(user_data)
#         users.append(user)
#     return users
