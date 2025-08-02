from typing import Annotated
from fastapi import APIRouter, BackgroundTasks
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.user.model import User
from .schema import (
    AccessTokenResp,
    RefreshTokenReq,
    RefreshTokenResp,
    ForgotPasswordReq,
    ResetPasswordReq,
)
from ..dependencies.auth_dep import (
    get_current_user,
    get_auth_service,
)

from ..authentication.service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/access-token", response_model=AccessTokenResp)
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user credentials and return access and refresh tokens.
    This endpoint is designed to be compatible with OAuth2 password flow.
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = await auth_service.create_auth_tokens(user.id)

    return tokens


@router.post("/refresh-token", response_model=RefreshTokenResp)
async def refresh_access_token(
    payload: RefreshTokenReq,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint to refresh the access token using the refresh token.
    """

    return await auth_service.refresh_access_token(payload.token)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ForgotPasswordReq,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint to handle forgot password functionality.
    This should send a reset link to the user's email.
    """
    await auth_service.generate_and_send_otp(payload.email, background_tasks)
    return {"message": "OTP sent"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordReq,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint to reset the user's password.
    """
    return "Reset password endpoint"
