from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class AccessTokenResp(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenReq(BaseModel):
    token: str = Field(...)


class RefreshTokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
