from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from ..user.schema import CreateUser, UpdateUser
from ..models import User


class UserRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, user_data: CreateUser) -> User:
        """Creates a new user in the database."""
        new_user = User(
            email=user_data.email,
            hashed_password=user_data.password,
            role=user_data.role,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    # async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
    #     """
    #     Get a user by their ID.
    #     """
    #     query = select(User).where(User.id == user_id)
    #     result = await self.db.execute(query)

    #     return result.scalars().first()

    async def get_user_by_id(self, id: str) -> User | None:
        """
        Get a user by their ID.
        """
        user = select(User).where(User.id == id)
        result = await self.db.execute(user)
        if not result:
            return None
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> User | None:
        user = select(User).where(User.email == email)
        result = await self.db.execute(user)
        return result.scalars().first()

    async def update_user(self, user_id: str, payload: UpdateUser):
        user = await self.get_user_by_id(user_id)

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user_password(self, user_id: str, new_password: str):
        user = await self.get_user_by_id(user_id)
        user.hashed_password = new_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: str):
        user = await self.get_user_by_id(user_id)
        await self.db.delete(user)
        await self.db.commit()
