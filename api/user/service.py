from fastapi import HTTPException, status
from .schema import CreateUser, UpdateUser
from .model import User
from api.config.database import get_db_session
from api.utils.auth import hash_password
from ..shared.user_repo import UserRepository


class UserService:

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register_user(self, user_data: CreateUser) -> User:
        """
        Registers a new user.
        Handles password hashing and checks for existing users.
        """
        existing_user = await self.user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email already exists",
            )
        hashed_password = hash_password(user_data.password)

        user_data_for_repo = CreateUser(
            email=user_data.email,
            password=hashed_password,
        )
        return await self.user_repo.create_user(user_data_for_repo)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """
        Retrieves a user by their ID.
        """
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def update_user(self, user_id: str, payload: UpdateUser) -> User:
        """
        Updates user information.
        """
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        updated_user = await self.user_repo.update_user(user_id,payload)
        return updated_user

    async def delete_user(self, user_id: str) -> None:
        """Deletes a user by ID."""
        user_to_delete = await self.user_repo.get_user_by_id(user_id)
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        await self.user_repo.delete_user(user_id)
