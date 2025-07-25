from fastapi import APIRouter

router = APIRouter(prefix="/blog", tags=["Blogs"])


@router.post("/create-blog")
async def create_blog():
    return "Create blog endpoint"


@router.get("/get-blog")
async def get_blog():
    return "Get blog endpoint"


@router.put("/update-blog")
async def update_blog():
    return "Update blog endpoint"


@router.delete("/delete-blog")
async def delete_blog():
    return "Delete blog endpoint"


@router.get("/get-all-blogs")
async def get_all_blogs():
    return "Get all blogs endpoint"


@router.post("/like-blog")
async def like_blog():
    return "Like blog endpoint"


@router.post("/unlike-blog")
async def unlike_blog():
    return "Unlike blog endpoint"


@router.post("/comment-blog")
async def comment_blog():
    return "Comment blog endpoint"


@router.delete("/delete-comment")
async def delete_comment():
    return "Delete comment endpoint"


@router.get("/get-comments")
async def get_comments():
    return "Get comments endpoint"
