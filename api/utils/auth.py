from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import jwt
from jwt import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext

from fastapi import HTTPException, status
from ..config.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password: str) -> str:
    """
    Converts plain password to hashed value

    Args:
        password(str): Password to be hashed

    Returns:
        hashed-value(str): The hashed value of the input password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Token Management ---
def create_jwt_token(
    data: dict,
    secret_key: str,
    expires_delta: Optional[timedelta] = None,
    is_refresh_token: bool = False,
) -> str:
    """
    Creates a JWT token.
    'data' should contain claims like 'sub' (subject, e.g., user ID).
    """
    to_encode = data.copy()

    # Convert UUIDs to string for JWT claims
    if "sub" in to_encode and isinstance(to_encode["sub"], uuid.UUID):
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration if not provided (e.g., 15 minutes for access tokens)
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expires_minute
        )

    to_encode.update({"exp": expire.timestamp()})

    if is_refresh_token:
        to_encode.update({"refresh": True})

    encoded_jwt = jwt.encode(
        to_encode,
        key=secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def decode_jwt_token(token: str, secret_key: str) -> dict:
    """
    Decodes a JWT token. Raises exceptions for invalid or expired tokens.
    """
    try:
        payload = jwt.decode(
            token,
            key=secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
