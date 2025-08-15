from fastapi import HTTPException

"""
Custom exceptions for the Flash Blog API.
"""


class FlashBlogException(HTTPException):
    """Base exception class for Flash Blog."""

    def __init__(self, status_code: int, detail: str, extra_data: dict = None):
        self.extra_data = extra_data or {}
        super().__init__(status_code=status_code, detail=detail)


class BlogNotFoundError(FlashBlogException):
    """Raised when a requested blog is not found."""

    def __init__(self, resource_id: int):
        detail = f"Blog with ID {resource_id} not found"
        super().__init__(
            status_code=404,
            detail=detail,
            extra_data={"resource_id": resource_id},
        )


class UnauthorizedError(FlashBlogException):
    """Raised when user lacks permission for the requested action."""

    pass


class ValidationError(FlashBlogException):
    """Raised when data validation fails."""

    pass


class SlugConflictError(FlashBlogException):
    """Raised when unable to generate unique slug."""

    pass


class TagNotFoundError(FlashBlogException):
    """Raised when requested tags don't exist."""

    pass


class UserNotFoundError(FlashBlogException):
    """Raised when a requested user is not found."""

    pass
