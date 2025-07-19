from pydantic import BaseModel, EmailStr, Field, UUID4


class UserBase(BaseModel):
    full_name: str | None = None
    email: EmailStr = Field(...)


class CreateUser(UserBase):
    password: str = Field(...)


class CreateUserResp(BaseModel):
    id: UUID4
    user_info: UserBase

class AccessTokenResp(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenReq(BaseModel):
    token: str = Field(...)
class RefreshTokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"


