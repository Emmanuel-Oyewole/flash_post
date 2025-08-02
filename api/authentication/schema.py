from pydantic import BaseModel, EmailStr, Field


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

class ForgotPasswordReq(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user requesting password reset")

class ResetPasswordReq(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user resetting the password")
    otp_code: str = Field(..., description="One-time password code for resetting the password")
    new_password: str = Field(..., min_length=8, description="New password to set for the user")
