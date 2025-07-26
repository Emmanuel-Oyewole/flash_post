from pydantic import BaseModel, EmailStr, Field, UUID4
from datetime import datetime

class PublicUser(BaseModel):
    full_name: str | None = None
    email: EmailStr
    created_at: datetime
    avatar: str | None = None
