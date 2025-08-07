from fastapi import APIRouter

router = APIRouter(prefix="/blog", tags=["Blogs"])


@router.post("/")
async def create_blog():
    return "Create blog endpoint"


@router.get("/")
async def list_blogs():
    return "List all blogs endpoint"


@router.get("/{blog_id}")
async def get_blog(blog_id: str):
    return f"Get a specific blog endpoint: {blog_id}"


@router.get("/slug/{slug}")
async def get_blog_by_slug(slug: str):
    return f"Get blog by slug endpoint: {slug}"


@router.put("/{blog_id}")
async def update_blog(blog_id: str):
    return f"Update blog endpoint: {blog_id}"


@router.delete("/{blog_id}")
async def delete_blog(blog_id: str):
    return f"Delete blog endpoint: {blog_id}"


@router.post("/{blog_id}/publish")
async def publish_blog(blog_id: str):
    return f"Publish blog endpoint: {blog_id}"

@router.post("/{blog_id}/unpublish")
async def unpublish_blog(blog_id: str):
    return f"Unpublish blog endpoint: {blog_id}"

