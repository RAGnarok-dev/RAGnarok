from typing import Optional
from fastapi import Depends, Body
from fastapi import Response as FastAPIResponse
from ragnarok_server.service.user import user_service
from ragnarok_server.rdb.models import User
from ragnarok_server.router.base import(
    CustomAPIRouter,
    UserRegisterRequestModel,
    UserRegisterResponseModel,
    UserLoginRequestModel,
    UserLoginResponseModel
)
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.exceptions import InvalidArgsError
from ragnarok_server.auth import get_current_user

router = CustomAPIRouter(prefix="/users", tags=["User"])


@router.post(
    "/register",
    summary="Register a new user",
    response_model=Response[UserRegisterResponseModel],
)
async def register_user(
    register_data: UserRegisterRequestModel = Body(...),
    service=Depends(lambda: user_service),
) -> Response[UserRegisterResponseModel]:
    """
    Register a new user account using email, password, and username.
    """
    user: User = await service.register_user(
        register_data.email,
        register_data.password,
        register_data.username
    )
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
    login_data: UserLoginRequestModel = Body(...),
    service=Depends(lambda: user_service),
    response: FastAPIResponse = None,
) -> Response[UserLoginResponseModel]:
    """
    Authenticate a user by either username or email.
    If the user is already authenticated, return their details without requiring a new login.
    """
    if not login_data.username and not login_data.email:
        raise InvalidArgsError("Either username or email must be provided")

    result: dict = await service.login_user(
        login_data.email,
        login_data.username,
        login_data.password
    )
    user = result["user"]

    response.headers["Authorization"] = f"{result['token_type']} {result['access_token']}"

    return ResponseCode.OK.to_response(
        data=UserLoginResponseModel(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
    )

