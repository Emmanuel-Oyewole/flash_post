from datetime import timedelta, datetime
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db_session
from passlib.context import CryptContext
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError
from ..config.settings import settings
from ..user.service import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/access-token")


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
        self._pwd_context = CryptContext(schemes=["bcrypt"])

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, email: str, password: str):
        user = await self._user_repo.get_user_by_email(email)
        print(f"Authenticating user: {user}")
        if not (user and self._verify_password(password, user.hashed_password)):
            return None

        return user

    def create_access_token(self, subject: dict) -> str:
        """
        Create a JWT token with the user information.
        """
        to_encode = subject.copy()
        if "sub" in to_encode and isinstance(to_encode["sub"], uuid.UUID):
            to_encode["sub"] = str(to_encode["sub"])
        expire = datetime.now() + timedelta(
            minutes=settings.access_token_expires_minute
        )
        to_encode.update({"exp": expire.timestamp()})
        encoded_jwt = jwt.encode(
            to_encode,
            key=settings.access_token_secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    def create_refresh_token(self, subject: dict) -> str:
        """
        Create a JWT refresh token with the user information.
        """
        to_encode = subject.copy()
        if "sub" in to_encode and isinstance(to_encode["sub"], uuid.UUID):
            to_encode["sub"] = str(to_encode["sub"])  # Convert UUID to string
        expire = datetime.now() + timedelta(days=settings.refresh_token_expires_day)
        to_encode.update({"exp": expire.timestamp(), "refresh": True})
        encoded_jwt = jwt.encode(
            to_encode,
            key=settings.refresh_token_secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_session)
    ) -> dict:
        pass

    async def _decode_token(self, token: str) -> dict | None:
        """
        Decode the JWT token to extract user information.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token,
                key=settings.refresh_token_secret_key,
                algorithms=[settings.algorithm],
            )
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                raise credentials_exception

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except (InvalidTokenError, PyJWTError):
            raise credentials_exception
        user = await self._user_repo.get_user_by_id(user_id)

        if user is None:
            raise credentials_exception
        return user


def get_auth_service() -> AuthService:
    return AuthService()
