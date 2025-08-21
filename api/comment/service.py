from fastapi import status
from .schema import CommentCreate, CommentResponse
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..shared.user_repo import UserRepository
from ..exceptions.exceptions import BlogNotFoundError, CommentError, UnauthorizedError
from ..user.model import User
from ..shared.pagination import PaginatedResponse, PaginationParams


class CommentService:

    def __init__(
        self,
        comment_repo: CommentRepository,
        blog_repo: BlogRepository,
        user_repo: UserRepository,
    ) -> None:
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

    async def get_comment(self, comment_id: str) -> CommentResponse:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise Exception("Comment not found")
        return CommentResponse.model_validate(comment)

    async def list_comments(
        self, blog_id: str, pagination: PaginationParams
    ) -> PaginatedResponse[CommentResponse]:

        paginated_comments = await self.comment_repo.list_by_blog(blog_id, pagination)
        # You may want to count total comments for pagination metadata
        return PaginatedResponse(
            items=[
                CommentResponse.model_validate(comment)
                for comment in paginated_comments.items
            ],
            total=paginated_comments.total,
            page=paginated_comments.page,
            per_page=paginated_comments.per_page,
            has_next=paginated_comments.has_next,
            has_prev=paginated_comments.has_next,
        )
