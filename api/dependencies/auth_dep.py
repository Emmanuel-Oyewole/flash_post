from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from ..config.database import get_db_session
from ..shared.user_repo import UserRepository
from ..user.service import UserService
from ..user.model import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/access-token")


async def get_user_repo(db: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """
    Dependency to get the UserRepository instance.
    """
    return UserRepository(db)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    """Dependency to provide a UserService instance."""
    return UserService(user_repo)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
):
    """
    Dependency to get the AuthService instance.
    """
    from ..authentication.service import AuthService

    return AuthService(user_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme), auth_service=Depends(get_auth_service)
) -> User:
    """
    Dependency to get the current authenticated user from an access token.
    This will be used in your protected API routes.
    """
    return await auth_service.get_current_user_from_jwt(token)
