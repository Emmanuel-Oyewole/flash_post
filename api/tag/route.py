from fastapi import APIRouter


router = APIRouter(prefix="/tag", tags=["Tags"])


@router.get("/tags")
async def get_tags():
    """
    Retrieve a list of tags.
    """
    return {"tags": ["tag1", "tag2", "tag3"]}


@router.post("/tags")
async def create_tag(tag: str):
    """
    Create a new tag.
    """
    return {"message": f"Tag '{tag}' created successfully."}


@router.get("/tags/{tag_id}")
async def get_tag(tag_id: int):
    """
    Retrieve a specific tag by its ID.
    """
    return {"tag_id": tag_id, "tag_name": f"tag{tag_id}"}


@router.put("/tags/{tag_id}")
async def update_tag(tag_id: int, tag: str):
    """
    Update an existing tag by its ID.
    """
    return {"message": f"Tag '{tag}' updated successfully for tag ID {tag_id}."}


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int):
    """
    Delete a tag by its ID.
    """
    return {"message": f"Tag with ID {tag_id} deleted successfully."}


@router.get("/tags/{tag_id}/blogs")
async def get_blogs_by_tag(tag_id: int):
    """
    Paginated list of blogs with specific tag
    """
    return {"tag_id": tag_id, "blogs": ["blog1", "blog2", "blog3"]}
