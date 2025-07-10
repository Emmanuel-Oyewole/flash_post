from fastapi import APIRouter, Depends, HTTPException, status
from .schema import CreateUser
from api.user.service import get_user_repo, UserRepository

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/register")
async def register_user(
    payload: CreateUser, user_repo: UserRepository = Depends(get_user_repo)
):
    user_exit = await user_repo.get_by_email(payload.email)
    if user_exit:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided email is already in use",
        )

    return await user_repo.register_user(payload)
