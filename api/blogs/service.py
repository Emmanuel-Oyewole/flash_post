from ..shared.blog_repo import BlogRepository
class BlogService:
    def __init__(self, blog_repo: BlogRepository) -> None:
        self.blog_repo = blog_repo