from datetime import timedelta
import uuid
from fastapi import BackgroundTasks, HTTPException, status

from api.shared.otp_repo import OTPRepository
from api.user.model import User
from ..config.settings import settings
from ..config.helpers import logger
from ..user.service import UserRepository
from .schema import TokenResponse
from ..utils.auth import create_jwt_token, decode_jwt_token
from ..utils.auth import verify_password, hash_password
from ..utils.otp_helper import verify_otp_code
from ..shared.otp_repo import OTPRepository
from ..notification.service import NotificationService


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        otp_repo: OTPRepository,
        notification_service: NotificationService,
    ) -> None:
        self._user_repo = user_repo
        self._otp_repo = otp_repo
        self._notification_service = notification_service

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

    async def generate_and_send_otp(
        self, email: str, background_tasks: BackgroundTasks
    ) -> None:
        """
        Generates and sends one-time password (OTP) for the user.
        """
        user = await self._user_repo.get_user_by_email(email)
        if not user:
            logger.info(f"User with email {email} not found for OTP generation.")
            return
        otp_code = str(uuid.uuid4().int)[:6]  # Generate a 6-digit OTP
        # Cache the OTP in Redis
        await self._otp_repo.cache_otp(user.id, otp_code)

        logger.info(f"sending OTP {otp_code} to user {user.email}")

        # Send the OTP via email
        await self._notification_service.send_reset_password_email(
            email=email,
            otp_code=otp_code,
            background_tasks=background_tasks,
        )

    async def verify_otp_and_update_password(
        self, email: str, otp: str, new_password: str, background_tasks: BackgroundTasks
    ) -> User:
        """
        Verifies the provided OTP for the user.
        Returns the user if the OTP is valid, raises an error otherwise.
        """
        user = await self._user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email address",
            )

        # retrieve hashed the cached OTP from Redis
        cached_otp = await self._otp_repo.get_otp(user.id)

        if not cached_otp or not verify_otp_code(otp, cached_otp):
            logger.info(f"Invalid OTP {otp} for user {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        # Invalidate the OTP after successful verification
        await self._otp_repo.delete_otp(user.id)
        # Update the user's password
        hashed_password = hash_password(new_password)
        await self._user_repo.update_user_password(user.id, hashed_password)
        logger.info(f"Password updated successfully for user {email}")

        await self._notification_service.send_reset_password_confirmation(email, background_tasks)

        return user
