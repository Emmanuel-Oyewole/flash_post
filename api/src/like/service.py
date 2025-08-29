from typing import Literal
from ..shared.like_repo import LikeRepository
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..models.blog_model import Blog
from ..models.comment_model import Comment


class LikeService:

    def __init__(
        self,
        like_repo: LikeRepository,
        blog_repo: BlogRepository,
        comment_repo: CommentRepository,
    ):
        self.like_repo = like_repo
        self.blog_repo = blog_repo
        self.comment_repo = comment_repo

    async def like(
        self, user_id: str, target_id: str, target_type: Literal["blog", "comment"]
    ) -> Blog | Comment:
        if target_type == "blog":
            await self.blog_repo.get_by_id(target_id)
            await self.like_repo.create_like(user_id, target_id, target_type)
            await self.blog_repo.increment_like_count(target_id)
            return await self.blog_repo.get_by_id(target_id)
            

        await self.comment_repo.get_by_id(target_id)
        await self.like_repo.create_like(user_id, target_id, target_type)
        await self.comment_repo.increment_like_count(target_id)
        return await self.comment_repo.get_by_id(target_id)

    async def unlike(
        self, user_id: str, target_id: str, target_type: Literal["blog", "comment"]
    ):
        if target_type == "blog":
            await self.blog_repo.get_by_id(target_id)
            await self.like_repo.delete_like(user_id, target_id, target_type)
            await self.blog_repo.decrement_like_count(target_id)
            return await self.blog_repo.get_by_id(target_id)
        
        await self.comment_repo.get_by_id(target_id)
        await self.like_repo.delete_like(user_id, target_id, target_type)
        await self.comment_repo.decrement_like_count(target_id)
        return await self.comment_repo.get_by_id(target_id)
