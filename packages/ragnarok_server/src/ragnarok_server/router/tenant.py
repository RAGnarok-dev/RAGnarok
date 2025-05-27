from fastapi import Body, Depends
from fastapi import Response as FastAPIResponse
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.exceptions import InvalidArgsError
from ragnarok_server.rdb.models import Tenant
from ragnarok_server.router.base import (
    CustomAPIRouter,
    TenantLoginRequestModel,
    TenantLoginResponseModel,
    TenantRegisterRequestModel,
    TenantRegisterResponseModel,
)
from ragnarok_server.service.odb import odb_service
from ragnarok_server.service.tenant import tenant_service

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

    await odb_service.create_bucket(bucket_name=f"tenant-{tenant.id}")

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
