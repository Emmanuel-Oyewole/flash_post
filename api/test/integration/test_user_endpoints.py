import pytest
from httpx import AsyncClient
from fastapi import status

from ...src.user.schema import CreateUser, UpdateUser


@pytest.mark.integration
class TestUserEndpoints:
    """Integration tests for user API endpoints."""

    async def test_register_user_success(
        self, client: AsyncClient, override_get_db, override_user_service
    ):
        """Test successful user registration."""
        user_data = CreateUser(email="flashpostuser@gmail.com", password="password123")

        response = await client.post("/user/register", json=user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "user_info" in data
        assert data["user_info"]["email"] == user_data["email"]
        assert "password" not in data["user_info"]  # Ensure password is not returned
