from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from ..shared.schema import PublicUser


class UserBase(BaseModel):
    full_name: str | None = None
    email: EmailStr = Field(...)


class UpdateUser(UserBase):
    pass


class GetUser(PublicUser):
 pass


class CreateUser(UserBase):
    password: str = Field(...)


class PublicUserResp(BaseModel):
    id: UUID
    user_info: PublicUser
