"""
Integration tests for Authentication endpoints.

This demonstrates:
- Testing authentication flows
- JWT token validation
- Password hashing
- Error scenarios
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from ...src.models.user_model import User, UserRole
from ..factories.user import UserFactory


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""

    async def test_user_registration_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful user registration."""
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        response = await client.post("/auth/register", json=registration_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == registration_data["email"]
        assert data["first_name"] == registration_data["first_name"]
        assert "id" in data
        assert "hashed_password" not in data  # Ensure password is not exposed

    async def test_user_registration_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test registration with existing email."""
        # Create existing user
        existing_user = UserFactory.create(email="existing@example.com")
        await db_session.commit()

        registration_data = {
            "email": "existing@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        response = await client.post("/auth/register", json=registration_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "invalid_data,expected_error",
        [
            ({"email": "invalid-email", "password": "password123"}, "email"),
            ({"email": "valid@email.com", "password": "123"}, "password"),
            ({"email": "valid@email.com"}, "password"),
            ({"password": "validpassword123"}, "email"),
        ],
    )
    async def test_user_registration_validation(
        self, client: AsyncClient, invalid_data: dict, expected_error: str
    ):
        """Test registration validation with various invalid inputs."""
        response = await client.post("/auth/register", json=invalid_data)

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(expected_error in str(error).lower() for error in error_detail)

    async def test_user_login_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful user login."""
        # Create user with known password
        password = "testpassword123"
        user = UserFactory.create(password=password)
        await db_session.commit()

        login_data = {
            "username": user.email,  # FastAPI OAuth2PasswordRequestForm uses 'username'
            "password": password,
        }

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_user_login_invalid_credentials(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with invalid credentials."""
        user = UserFactory.create()
        await db_session.commit()

        login_data = {"username": user.email, "password": "wrongpassword"}

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_user_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {"username": "nonexistent@example.com", "password": "anypassword"}

        response = await client.post("/auth/login", data=login_data)

        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token(
        self, client: AsyncClient, authenticated_user: dict
    ):
        """Test accessing protected endpoint with valid token."""
        response = await client.get(
            "/user/profile",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(authenticated_user["user"]["id"])

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/user/profile")

        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            "/user/profile", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_token_refresh(self, client: AsyncClient, authenticated_user: dict):
        """Test token refresh functionality."""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}

        response = await client.post("/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_logout(self, client: AsyncClient, authenticated_user: dict):
        """Test user logout."""
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
        )

        assert response.status_code == 200

    async def test_user_roles(self, client: AsyncClient, db_session: AsyncSession):
        """Test user role assignment and verification."""
        # Create admin user
        admin_user = UserFactory.create(role=UserRole.ADMIN)
        regular_user = UserFactory.create(role=UserRole.USER)
        await db_session.commit()

        assert admin_user.role == UserRole.ADMIN
        assert regular_user.role == UserRole.USER


class TestPasswordSecurity:
    """Test password hashing and security."""

    async def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        from ...src.utils.auth import hash_password, verify_password

        password = "mySecurePassword123!"
        hashed = hash_password(password)

        # Password should be hashed
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 characters

        # Should verify correctly
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    async def test_user_factory_password_handling(self, db_session: AsyncSession):
        """Test that UserFactory handles passwords correctly."""
        password = "testpassword123"
        user = UserFactory.create(password=password)

        # Password should be hashed in database
        assert user.hashed_password != password

        # Should be able to verify the password
        from ...src.utils.auth import verify_password

        assert verify_password(password, user.hashed_password) is True


class TestAuthenticationHelpers:
    """Test authentication utility functions."""

    async def test_jwt_token_creation_and_validation(self):
        """Test JWT token creation and validation."""
        from ...src.utils.auth import create_access_token, verify_token

        user_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data=user_data)

        assert token is not None
        assert isinstance(token, str)

        # Verify token
        decoded_data = verify_token(token)
        assert decoded_data["sub"] == user_data["sub"]
        assert decoded_data["user_id"] == user_data["user_id"]

    async def test_expired_token_handling(self):
        """Test handling of expired tokens."""
        from ...src.utils.auth import create_access_token, verify_token
        from datetime import timedelta

        # Create token with very short expiry
        user_data = {"sub": "test@example.com"}
        token = create_access_token(
            data=user_data, expires_delta=timedelta(seconds=-1)  # Already expired
        )

        # Should raise exception when verifying expired token
        with pytest.raises(Exception):
            verify_token(token)
