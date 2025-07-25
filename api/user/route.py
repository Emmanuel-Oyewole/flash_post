from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from api.config.database import get_db_session
from api.user.model import User
from .schema import UpdateUser
from .service import UserService
from ..dependencies.auth_dep import get_auth_service
from ..dependencies.auth_dep import get_current_user, get_user_service


router = APIRouter(prefix="/user", tags=["User-Crud"])


@router.put("/update-profile/{user_id}", status_code=status.HTTP_200_OK)
async def update_profile(
    user_id: str,
    payload: UpdateUser,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint to update user profile information.
    """
    try:
        user = await user_service.update_user(user_id, payload)
        return user
    except HTTPException as e:
        raise e



# @router.put("update-profile-picture")
# async def update_profile_picture():
#     return "Update profile picture endpoint"


@router.get("/me")
async def get_my_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/delete-account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.delete_user(str(current_user.id))
    return {"detail": "Account deleted successfully"}
