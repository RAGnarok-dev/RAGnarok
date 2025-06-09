from fastapi import Body
from fastapi import Depends
import os
import base64
from fastapi import Response as FastAPIResponse
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.exceptions import InvalidArgsError, NoResultFoundError
from ragnarok_server.rdb.models import Tenant, User
from ragnarok_server.router.base import (
    CustomAPIRouter,
    TenantGetUsersResponseModel,
    TenantInfoResponseModel,
    TenantInviteRequestModel,
    TenantInviteResponseModel,
    TenantLoginRequestModel,
    TenantLoginResponseModel,
    TenantRegisterRequestModel,
    TenantRegisterResponseModel,
    TenantRemoveUserRequestModel,
    TenantRemoveUserResponseModel,
    UserInfoResponseModel,
    TenantUpdateAvatarRequestModel,
    TenantUpdateAvatarResponseModel,
    TenantChangePasswordRequestModel,
    TenantChangePasswordResponseModel
)
from ragnarok_server.auth import get_current_tenant
from passlib.context import CryptContext
from ragnarok_server.service.store import store_service
from ragnarok_server.service.tenant import tenant_service
from ragnarok_server.service.user import user_service
from fastapi.security import OAuth2PasswordBearer
from ragnarok_server.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth.py/token")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = CustomAPIRouter(prefix="/tenants", tags=["Tenant"])


@router.post(
    "/register",
    summary="Register a new tenant",
    response_model=Response[TenantRegisterResponseModel],
)
async def register_tenant(
    register_data: TenantRegisterRequestModel = Body(...),
    service=Depends(lambda: tenant_service),
) -> Response[TenantRegisterResponseModel]:
    """
    Register a new tenant account using email, password, and name.
    """
    tenant: Tenant = await service.register_tenant(
        register_data.email, register_data.password, register_data.tenantname
    )

    await store_service.create_bucket(principal_type="tenant", principal_id=tenant.id)

    return ResponseCode.OK.to_response(
        data=TenantRegisterResponseModel(
            id=tenant.id, tenantname=tenant.name, email=tenant.email, is_active=tenant.is_active
        )
    )


@router.post(
    "/login",
    summary="Login an existing tenant",
    response_model=Response[TenantLoginResponseModel],
)
async def login_tenant(
    login_data: TenantLoginRequestModel = Body(...),
    service=Depends(lambda: tenant_service),
    response: FastAPIResponse = None,
) -> Response[TenantLoginResponseModel]:
    """
    Authenticate a user by either tenantname or email.
    If the tenant is already authenticated, return their details without requiring a new login.
    """
    if not login_data.tenantname and not login_data.email:
        raise InvalidArgsError("Either tenantname or email must be provided")

    result: dict = await service.login_tenant(login_data.email, login_data.tenantname, login_data.password)

    tenant = result["tenant"]

    response.headers["Authorization"] = f"{result['token_type']} {result['access_token']}"
    response.headers["Access-Control-Request-Headers"] = "Authorization"

    return ResponseCode.OK.to_response(
        data=TenantLoginResponseModel(
            id=tenant.id,
            tenantname=tenant.name,
            email=tenant.email,
            is_active=tenant.is_active,
            access_token=result["access_token"],
            token_type=result["token_type"],
        )
    )


@router.post(
    "/invite",
    summary="Invite a user to a tenant by email",
    response_model=Response[TenantInviteResponseModel],
)
async def invite_user_to_tenant_by_email(
    data: TenantInviteRequestModel = Body(...),
    service=Depends(lambda: tenant_service),
) -> Response[TenantInviteResponseModel]:
    """
    Invite a user to a tenant by looking up their email.
    """
    user = await service.invite_user_to_tenant(data.tenant_id, data.user_email)

    if not user:
        raise NoResultFoundError("No User Find")

    return ResponseCode.OK.to_response(
        data=TenantInviteResponseModel(
            user_id=user.id, username=user.username, user_email=user.email, tenant_id=data.tenant_id
        )
    )


@router.post(
    "/remove",
    summary="Remove a user from a tenant by email",
    response_model=Response[TenantRemoveUserResponseModel],
)
async def remove_user_from_tenant(
    data: TenantRemoveUserRequestModel = Body(...),
    service=Depends(lambda: tenant_service),
) -> Response[TenantRemoveUserResponseModel]:
    """
    Remove a user from a tenant by looking up their email.
    """
    user = await service.remove_user_from_tenant(data.tenant_id, data.user_email)

    if not user:
        raise NoResultFoundError("No User Found in the Specified Tenant")

    return ResponseCode.OK.to_response(
        data=TenantRemoveUserResponseModel(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            tenant_id=data.tenant_id,
        )
    )


@router.get(
    "/info",
    summary="Get an existing tenant info",
    response_model=Response[TenantInfoResponseModel],
)
async def get_tenant_info(
    current_tenant: Tenant = Depends(get_current_tenant), service=Depends(lambda: tenant_service)
) -> Response[TenantInfoResponseModel]:

    result: dict = await service.get_tenant_info(current_tenant)

    return ResponseCode.OK.to_response(
        data=TenantInfoResponseModel(
            tenantname=result["tenantname"],
            id=result["id"],
            avatar=result["avatar"],
            email=result["email"]
        )
    )


@router.get(
    "/get_users",
    summary="Tenants obtain all user information",
    response_model=Response[TenantGetUsersResponseModel],
)
async def get_all_users_info(
        token: str = Depends(oauth2_scheme), service=Depends(lambda: tenant_service)
) -> Response[TenantGetUsersResponseModel]:
    token_data = await decode_access_token(token)
    if token_data.principal_type == 'tenant':
        current_tenant: Tenant = await service.get_tenant_by_id(token_data.principal_id)
    else:
        tenant_id = await user_service.get_tenant_id_by_user_id(token_data.principal_id)
        if tenant_id is None:
            return ResponseCode.OK.to_response(
                data=TenantGetUsersResponseModel(
                    tenant_id=1,
                    tenantname="1",
                    users=[]
                )
            )
        current_tenant: Tenant = await service.get_tenant_by_id(tenant_id)

    users: list[User] = await service.get_all_users_info(current_tenant)

    user_data = [UserInfoResponseModel(id=user.id, username=user.username, email=user.email, avatar=user.avatar_url)
                 for user in users]

    return ResponseCode.OK.to_response(
        data=TenantGetUsersResponseModel(tenant_id=current_tenant.id, tenantname=current_tenant.name, users=user_data)
    )


@router.post(
    "/update_avatar",
    summary="Update tenant avatar",
    response_model=Response[TenantUpdateAvatarResponseModel],
)
async def update_tenant_avatar(
    data: TenantUpdateAvatarRequestModel = Body(...),
    current_tenant: Tenant = Depends(get_current_tenant),
    service=Depends(lambda: tenant_service)
) -> Response[TenantUpdateAvatarResponseModel]:
    header, encoded = data.avatar.split(',', 1)
    file_data = base64.b64decode(encoded)
    filename = f"{current_tenant.id}-tenant.png"
    save_dir = "static/avatars"

    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_data)

    new_tenant: Tenant = await service.update_tenant_avatar(current_tenant, data.avatar, data.tenantname)
    return ResponseCode.OK.to_response(
        data=TenantUpdateAvatarResponseModel(
            tenantname=new_tenant.name,
            tenant_id=new_tenant.id,
            avatar=new_tenant.avatar_url
        )
    )


@router.post(
    "/change_password",
    summary="Tenant change the password",
    response_model=Response[TenantChangePasswordResponseModel]
)
async def change_password(
        data: TenantChangePasswordRequestModel = Body(...),
        current_tenant: Tenant = Depends(get_current_tenant),
        service=Depends(lambda: tenant_service)
) -> Response[TenantChangePasswordResponseModel]:
    new_hashed_password = pwd_context.hash(data.new_password)

    new_tenant: Tenant = await service.change_password(current_tenant, data.password, new_hashed_password)

    return ResponseCode.OK.to_response(
        data=TenantChangePasswordResponseModel(
            tenantname=new_tenant.name,
            tenant_id=new_tenant.id,
            password_hash=new_tenant.password_hash
        )
    )
