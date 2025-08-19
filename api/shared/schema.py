import uuid
from pydantic import BaseModel, EmailStr, Field, UUID4, ConfigDict
from datetime import datetime


class PublicUser(BaseModel):
    id: uuid.UUID
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

    model_config = ConfigDict(from_attributes=True)
