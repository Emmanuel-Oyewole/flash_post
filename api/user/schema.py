from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    full_name: str | None = None
    email: EmailStr = Field(...)


class CreateUser(UserBase):
    password: str = Field(...)


class CreateUserResp(BaseModel):
    id: int
    user_info: UserBase
