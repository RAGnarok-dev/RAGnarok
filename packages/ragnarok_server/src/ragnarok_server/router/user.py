from fastapi import Depends, Query
from ragnarok_server.service.user import user_service
from ragnarok_server.rdb.models import User
from ragnarok_server.router.base import CustomAPIRouter, UserRegisterResponseModel
from ragnarok_server.common import Response, ResponseCode

router = CustomAPIRouter(prefix="/users", tags=["User"])


@router.post(
    "/register",
    summary="Register a new user",
    response_model=Response[UserRegisterResponseModel],
)
async def register_user(
    email: str = Query(..., description="User email, must be unique"),
    password: str = Query(..., description="User password (will be hashed)"),
    username: str = Query(..., description="username"),
    service=Depends(lambda: user_service),
) -> Response[UserRegisterResponseModel]:
    """
    Register a new user account using email, password, and username.
    """
    user: User = await service.register_user(email, password, username)
    return ResponseCode.OK.to_response(
        data=UserRegisterResponseModel(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )
    )
