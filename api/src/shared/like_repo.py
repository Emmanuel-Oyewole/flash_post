from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import status
from uuid import UUID
from ..models.like_model import Like
from ..exceptions.exceptions import LikeConflictError


class LikeRepository:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get_like(
        self, user_id: str, target_id: str, target_type: str
    ) -> Optional[Like]:
        stmt = select(Like)
        if target_type == "blog":
            stmt = stmt.where(Like.user_id == user_id, Like.blog_id == target_id)
        else:
            stmt = stmt.where(Like.user_id == user_id, Like.comment_id == target_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_like(self, user_id: str, target_id: str, target_type: str) -> Like:
        # Prevent duplicate like
        existing_like = await self.get_like(user_id, target_id, target_type)
        if existing_like:
            raise LikeConflictError(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"user with id: {user_id} already liked entity",
            )
        like_data = {
            "user_id": user_id,
            "blog_id": target_id if target_type == "blog" else None,
            "comment_id": target_id if target_type == "comment" else None,
        }
        like = Like(**like_data)
        self.db.add(like)
        await self.db.commit()
        await self.db.refresh(like)
        return like

    async def delete_like(self, user_id: str, target_id: str, target_type: str) -> bool:
        existing_like = await self.get_like(user_id, target_id, target_type)
        if not existing_like:
            raise LikeConflictError(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"user with id: {user_id} has not liked entity before",
            )
        await self.db.delete(existing_like)
        await self.db.commit()
        return True
