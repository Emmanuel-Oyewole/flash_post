from pydantic import BaseModel, EmailStr, Field, UUID4
from datetime import datetime

class PublicUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    email: EmailStr
    avatar: str | None = None
    role: str
    email_verified: bool 
    is_active: bool
    created_at: datetime
    updated_at: datetime
