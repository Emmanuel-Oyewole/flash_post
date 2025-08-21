from fastapi import status
from .schema import CommentCreate, CommentResponse
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..shared.user_repo import UserRepository
from ..exceptions.exceptions import BlogNotFoundError, CommentError, UnauthorizedError
from ..models import User


class CommentService:

    def __init__(
        self,
        comment_repo: CommentRepository,
        blog_repo: BlogRepository,
        user_repo: UserRepository,
    ):
        self.comment_repo = comment_repo
        self.blog_repo = blog_repo
        self.user_repo = user_repo

    async def create_comment(
        self, blog_id: str, author_id: str, data: CommentCreate
    ) -> CommentResponse:
        # current_user: User = await self.user_repo.get_user_by_id(author_id)
        # if not current_user.email_verified and current_user.is_active:
        #     raise UnauthorizedError(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="only active and verified user can comment on post",
        #     )

        blog = await self.blog_repo.get_by_id(blog_id=blog_id, include_drafts=True)
        if not blog:
            raise BlogNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"blog with blog id: {blog_id} does not exist",
            )

        if not blog.is_published:
            raise CommentError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="only published blog accepts comments",
            )

        comment_data = {
            "content": data.content,
            "blog_id": blog_id,
            "author_id": author_id,
            "parent_id": data.parent_id,
        }
        # 1. Create the new comment in the database.
        comment = await self.comment_repo.create(comment_data)

        comment_with_relation = await self.comment_repo.get_by_id(comment_id=comment.id)

        return CommentResponse.model_validate(comment_with_relation)
