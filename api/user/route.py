from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from api.config.database import get_db_session
from .schema import CreateUser, CreateUserResp, AccessTokenResp, RefreshTokenReq, RefreshTokenResp
from api.user.service import get_user_repo, UserRepository
from ..config.auth import AuthService, get_auth_service
from sqlalchemy.orm import Session


router = APIRouter(prefix="/user", tags=["User"])


@router.post("/register", response_model=CreateUserResp)
async def register_user(
    payload: CreateUser, user_repo: UserRepository = Depends(get_user_repo)
):
    user_exit = await user_repo.get_user_by_email(payload.email)
    if user_exit:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided email is already in use",
        )
    user = await user_repo.register_user(payload)
    return {"id": user.id, "user_info": user}


@router.post("/access-token", response_model=AccessTokenResp)
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db_session),
):
    """
    Endpoint to get access token for the user.
    """
    auth_service = AuthService(UserRepository(db))

    user_authenticate = await auth_service.authenticate_user(
        form_data.username, form_data.password
    )

    if user_authenticate is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(
        subject={"sub": user_authenticate.id}
    )

    refresh_token = auth_service.create_refresh_token(
        subject={"sub": str(user_authenticate.id), "refresh": True}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=RefreshTokenResp)
async def refresh_access_token(
    payload: RefreshTokenReq,
    db: Session = Depends(get_db_session),
):
    """
    Endpoint to refresh the access token using the refresh token.
    """
    auth_service = AuthService(UserRepository(db))

    user = await auth_service._decode_token(payload.token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        subject={"sub": str(user.id)}
    )

    return {"access_token": access_token, "token_type": "bearer"}