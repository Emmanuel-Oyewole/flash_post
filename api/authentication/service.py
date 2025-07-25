from datetime import timedelta
import uuid
from fastapi import HTTPException, status

from api.user.model import User
from ..config.settings import settings
from ..config.helpers import logger
from ..user.service import UserRepository
from .schema import TokenResponse
from ..utils.auth import create_jwt_token, decode_jwt_token
from ..utils.auth import verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authenticates a user by email and password.
        Returns the user object if successful, None otherwise.
        """
        user = await self._user_repo.get_user_by_email(email)

        logger.info(f"🔒🔒Trying to authenticate user with email: {email}")
        if not (user and verify_password(password, user.hashed_password)):
            return None
        return user

    async def create_auth_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        """
        Creates access and refresh tokens for a given user ID.
        """
        access_token_expires = timedelta(minutes=settings.access_token_expires_minute)
        refresh_token_expires = timedelta(days=settings.refresh_token_expires_day)

        token_payload = {"sub": str(user_id)}

        access_token = create_jwt_token(
            data=token_payload,
            secret_key=settings.access_token_secret_key,
            expires_delta=access_token_expires,
        )

        refresh_token = create_jwt_token(
            data=token_payload,
            secret_key=settings.refresh_token_secret_key,
            expires_delta=refresh_token_expires,
            is_refresh_token=True,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def get_current_user_from_jwt(self, token: str) -> User:
        """
        Validates an access token and returns the corresponding user.
        Raises HTTPException if the token is invalid or user not found.
        """
        payload = decode_jwt_token(
            token=token, secret_key=settings.access_token_secret_key
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self._user_repo.get_user_by_id(user_id_uuid)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refreshes the access token using the refresh token.
        """
        payload = decode_jwt_token(
            token=refresh_token, secret_key=settings.refresh_token_secret_key
        )

        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not a refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self._user_repo.get_user_by_id(user_id_uuid)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for refresh",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await self.create_auth_tokens(user.id)
