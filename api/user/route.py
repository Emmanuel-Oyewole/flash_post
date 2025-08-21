from fastapi import APIRouter, Depends, HTTPException, status

from ..models import User
from .schema import UpdateUser, CreateUser, PublicUserResp
from .service import UserService
from ..dependencies.auth_dep import get_current_user, get_user_service


router = APIRouter(prefix="/user", tags=["User-Crud"])


@router.post("/register", response_model=PublicUserResp)
async def register_user(
    payload: CreateUser, user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint to register a new user.
    """
    try:
        user = await user_service.register_user(payload)
        return {"id": user.id, "user_info": user}
    except Exception as e:
        raise e


@router.put(
    "/update-profile/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublicUserResp,
)
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
        return {"id": user.id, "user_info": user}
    except HTTPException as e:
        raise e


@router.get("/me", status_code=status.HTTP_200_OK, response_model=PublicUserResp)
async def get_my_info(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "user_info": current_user}


@router.delete("/delete-account/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.delete_user(user_id)
