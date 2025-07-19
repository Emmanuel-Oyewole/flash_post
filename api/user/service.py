from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import Depends
from .schema import CreateUser
from .model import User
from api.config.database import get_db_session
from api.utils.auth import hash_password


class UserRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    async def register_user(self, user_data: CreateUser) -> User:

        hashed_password = hash_password(user_data.password)
        new_user = User(
            hashed_password=hashed_password,
            email=user_data.email,
            full_name=user_data.full_name,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def get_user_by_id(self, id: int):
        user = select(User).where(User.id == id)
        result = await self.db.execute(user)
        if not result:
            return None
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> User | None:
        user = select(User).where(User.email == email)
        result = await self.db.execute(user)
        return result.scalars().first()

    async def update_user(self, email: str):
        pass

    async def delete_user(self, email: str):
        pass


async def get_user_repo(db: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(db)
