"""
Custom exceptions for the Flash Blog API.
"""

class FlashBlogException(Exception):
    """Base exception class for Flash Blog."""
    pass

class BlogNotFoundError(FlashBlogException):
    """Raised when a requested blog is not found."""
    pass

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