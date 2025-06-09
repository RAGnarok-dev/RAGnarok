from fastapi import Depends, Body
from fastapi import Response as FastAPIResponse
from ragnarok_server.service.user import user_service
from ragnarok_server.rdb.models import User
from ragnarok_server.rdb.engine import get_async_session
import os
import base64
from ragnarok_server.router.base import (
    CustomAPIRouter,
    UserRegisterRequestModel,
    UserRegisterResponseModel,
    UserLoginRequestModel,
    UserLoginResponseModel,
    UserInfoResponseModel,
    UserJoinTenantRequestModel,
    UserJoinTenantResponseModel,
    UserUpdateAvatarRequestModel,
    UserUpdateAvatarResponseModel,
    UserChangePasswordRequestModel,
    UserChangePasswordResponseModel
)
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.auth import get_current_user
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
    result: dict = await service.login_user(
        login_data.email,
        login_data.username,
        login_data.password
    )
    user = result["user"]

    response.headers["Authorization"] = f"{result['token_type']} {result['access_token']}"
    response.headers["Access-Control-Request-Headers"] = "Authorization"

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


@router.get(
    "/info",
    summary="Get an existing user info",
    response_model=Response[UserInfoResponseModel],
)
async def get_user_info(
    current_user: User = Depends(get_current_user),
    service=Depends(lambda: user_service)
) -> Response[UserInfoResponseModel]:

    result: dict = await service.get_user_info(current_user)

    return ResponseCode.OK.to_response(
        data=UserInfoResponseModel(
            username=result["username"],
            id=result["id"],
            avatar=result["avatar"],
            email=result["email"]
        )
    )


@router.post(
    "/join_tenant",
    summary="User want to join a tenant",
    response_model=Response[UserJoinTenantResponseModel],
)
async def join_tenant(
    join_data: UserJoinTenantRequestModel = Body(...),
    current_user: User = Depends(get_current_user),
    service=Depends(lambda: user_service)
) -> Response[UserJoinTenantResponseModel]:

    result: dict = service.join_tenant(
        join_data.tenant_id,
        current_user
    )

    return ResponseCode.OK.to_response(
        data=UserJoinTenantResponseModel(
            username=result["username"],
            user_id=result["user_id"],
            tenantname=result["tenantname"],
            tenant_id=result["tenant_id"]
        )
    )
@router.post(
    "/update_avatar",
    summary="Update user avatar",
    response_model=Response[UserUpdateAvatarResponseModel],
)
async def update_tenant_avatar(
    data: UserUpdateAvatarRequestModel = Body(...),
    current_user: User = Depends(get_current_user),
    service=Depends(lambda: user_service)
) -> Response[UserUpdateAvatarResponseModel]:
    header, encoded = data.avatar.split(',', 1)
    file_data = base64.b64decode(encoded)
    print(file_data)

    filename = f"{current_user.id}-user.png"
    save_dir = "static/avatars"

    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_data)

    new_avatar_url = f"/static/avatars/{filename}"

    new_user: User = await service.update_user_avatar(current_user, data.avatar, data.username)

    if new_user.username == data.username:
        return ResponseCode.OK.to_response(
            data=UserUpdateAvatarResponseModel(
                username=new_user.username,
                id=new_user.id,
                avatar=new_user.avatar_url
            )
        )
    else :
        return ResponseCode.INTERNAL_SERVER_ERROR.to_response(
            data=UserUpdateAvatarResponseModel(
                username=new_user.username,
                id=new_user.id,
                avatar=new_user.avatar_url
            )
        )
@router.get(
    "/logout",
    summary="User logout (no server state)"
)
async def logout():
    return {
        "code": 0,
        "message": "Logout successful"
    }

@router.post(
    "/change_password",
    summary="User change the password",
    response_model=Response[UserChangePasswordResponseModel]
)
async def change_password(
        data: UserChangePasswordRequestModel = Body(...),
        current_user: User = Depends(get_current_user),
        service=Depends(lambda: user_service)
) -> Response[UserChangePasswordResponseModel]:
    new_hashed_password = pwd_context.hash(data.new_password)

    new_user: User = await service.change_password(current_user, data.password, new_hashed_password)

    return ResponseCode.OK.to_response(
        data=UserChangePasswordResponseModel(
            username=new_user.username,
            id=new_user.id,
            password_hash=new_user.password_hash
        )
    )


