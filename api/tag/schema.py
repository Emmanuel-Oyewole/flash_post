from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TagBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color
    usage_count: int = 0
    created_at: Optional[datetime] = None   