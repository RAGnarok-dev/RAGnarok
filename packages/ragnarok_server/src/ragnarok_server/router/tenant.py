from fastapi import Body
from fastapi import Depends
from fastapi import Response as FastAPIResponse
from ragnarok_server.service.tenant import tenant_service
from ragnarok_server.rdb.models import Tenant, User
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.exceptions import InvalidArgsError, NoResultFoundError
from ragnarok_server.router.base import (
    CustomAPIRouter,
    TenantRegisterRequestModel,
    TenantRegisterResponseModel,
    TenantLoginResponseModel,
    TenantInviteRequestModel,
    TenantInviteResponseModel,
    TenantRemoveUserRequestModel,
    TenantRemoveUserResponseModel,
    TenantLoginRequestModel,
    TenantInfoResponseModel,
    TenantGetUsersResponseModel,
    UserInfoResponseModel,
    TenantUpdateAvatarRequestModel,
    TenantUpdateAvatarResponseModel,
)
from ragnarok_server.auth import get_current_tenant

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
        register_data.email,
        register_data.password,
        register_data.tenantname
    )
    return ResponseCode.OK.to_response(
        data=TenantRegisterResponseModel(
            id=tenant.id,
            tenantname=tenant.name,
            email=tenant.email,
            is_active=tenant.is_active
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

    result: dict = await service.login_tenant(
        login_data.email,
        login_data.tenantname,
        login_data.password
    )

    tenant = result["tenant"]

    response.headers["Authorization"] = f"{result['token_type']} {result['access_token']}"

    return ResponseCode.OK.to_response(
        data=TenantLoginResponseModel(
            id=tenant.id,
            tenantname=tenant.name,
            email=tenant.email,
            is_active=tenant.is_active,
            access_token=result["access_token"],
            token_type=result["token_type"]
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
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            tenant_id=data.tenant_id
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
    current_tenant: Tenant = Depends(get_current_tenant),
    service=Depends(lambda: tenant_service)
) -> Response[TenantInfoResponseModel]:

    result: dict = await service.get_tenant_info(current_tenant)

    return ResponseCode.OK.to_response(
        data=TenantInfoResponseModel(
            tenantname=result["tenantname"],
            id=result["id"],
            avatar="avatar"
        )
    )


@router.get(
    "/get_users",
    summary="Tenants obtain all user information",
    response_model=Response[TenantGetUsersResponseModel],
)
async def get_all_users_info(
    current_tenant: Tenant = Depends(get_current_tenant),
    service=Depends(lambda: tenant_service)
) -> Response[TenantGetUsersResponseModel]:
    users: list[User] = await service.get_all_users_info(current_tenant)

    user_data = [
        UserInfoResponseModel(
            id=user.id,
            username=user.username,
            avatar="avatar"
        )
        for user in users
    ]

    return ResponseCode.OK.to_response(
        data=TenantGetUsersResponseModel(
            tenant_id=current_tenant.id,
            tenantname=current_tenant.name,
            users=user_data
        )
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
    new_tenant: Tenant = await service.update_tenant_avatar(current_tenant, data.new_avatar_url)
    return ResponseCode.OK.to_response(
        data=TenantUpdateAvatarResponseModel(
            tenantname=new_tenant.name,
            tenant_id=new_tenant.id,
            avatar=new_tenant.avatar_url
        )
    )


