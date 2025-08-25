from fastapi import status
from .schema import CommentCreate, CommentResponse, CommentUpdate
from ..shared.comment_repo import CommentRepository
from ..shared.blog_repo import BlogRepository
from ..shared.user_repo import UserRepository
from ..exceptions.exceptions import (
    BlogNotFoundError,
    CommentError,
    UnauthorizedError,
    UnExpectedUpdateError,
)
from ..models import User
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
        comments_response = [
            CommentResponse.model_validate(comment)
            for comment in paginated_comments.items
        ]
        return PaginatedResponse(
            items=comments_response,
            total=paginated_comments.total,
            page=paginated_comments.page,
            total_pages=paginated_comments.total_pages,
            per_page=paginated_comments.per_page,
            has_next=paginated_comments.has_next,
            has_prev=paginated_comments.has_prev,
        )

    async def update_comment(
        self, comment_id: str, blog_id: str, data: CommentUpdate, user_id: str
    ) -> CommentResponse:
        blog = await self.blog_repo.get_by_id(blog_id)
        if not blog:
            raise BlogNotFoundError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"blog with id {blog_id} not found",
            )

        if not blog.is_published:
            raise UnauthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="only published blog can be comment on",
            )

        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise CommentError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"comment with Id: {comment_id} not found",
            )

        if comment.author_id != user_id or comment.blog_id != blog.id:
            raise UnauthorizedError(
                status_code=status.HTTP_409_CONFLICT,
                detail="either user is not the comment owner or comment is not associated to blog",
            )
        updated_comment = await self.comment_repo.update(
            blog_id=blog_id,
            comment_id=comment_id,
            user_id=user_id,
            content=data.content,
        )
        if not updated_comment:
            raise UnExpectedUpdateError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="error occurred while updating blog"
            )
        
        # Eagerly load the updated comment for the response
        fully_loaded_comment = await self.comment_repo.get_by_id(updated_comment.id)
        return CommentResponse.model_validate(fully_loaded_comment)
    
    async def delete_comment(self, blog_id: str, comment_id: str, user_id: str) -> bool:
    # 🔍 Step 3a: Check if comment exists
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
         raise CommentNotFoundError(f"Comment {comment_id} not found")
    
    # 🔍 Step 3b: Verify comment belongs to this blog
        if str(comment.blog_id) != str(blog_id):
         raise CommentNotFoundError("Comment does not belong to this blog")
    
    # 🔍 Step 3c: Check authorization (owner or admin)
        if str(comment.author_id) != str(user_id):
            user = await self.user_repo.get_by_id(user_id)
        if user.role != "admin":
            raise UnauthorizedError("You can only delete your own comments")
    
    # ✅ All checks passed, proceed to delete
        return await self.comment_repo.delete(blog_id, comment_id, user_id)
