from typing import Optional
from fastapi import Depends, Query
from ragnarok_server.service.user import user_service
from ragnarok_server.rdb.models import User
from ragnarok_server.router.base import CustomAPIRouter, UserRegisterResponseModel, UserLoginResponseModel
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.exceptions import InvalidArgsError, NoResultFoundError

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

@router.post(
    "/login",
    summary="Login an existing user",
    response_model=Response[UserLoginResponseModel],
)
async def login_user(
    username: Optional[str] = Query(None, description="User name"),
    email: Optional[str] = Query(None, description="User Email"),
    password: str = Query(..., description="User password"),
    service=Depends(lambda: user_service),
) -> Response[UserLoginResponseModel]:
    """
    Authenticate a user by either username or email.
    """
    if not username and not email:
        raise InvalidArgsError("Either username or email must be provided")

    user: User = await service.login_user(email, username, password)

    return ResponseCode.OK.to_response(
        data=UserLoginResponseModel(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )
    )

