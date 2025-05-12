from fastapi import Depends, Query
from ragnarok_server.service.tenant import tenant_service
from ragnarok_server.rdb.models import Tenant
from ragnarok_server.router.base import CustomAPIRouter,TenantRegisterResponseModel, TenantLoginResponseModel
from ragnarok_server.common import Response, ResponseCode


router = CustomAPIRouter(prefix="/tenants", tags=["Tenant"])

@router.post(
    "/register",
    summary="Register a new tenant",
    response_model=Response[TenantRegisterResponseModel],
)
async def register_tenant(
    email: str = Query(..., description="Tenant email, must be unique"),
    password: str = Query(..., description="Tenant password(will be hashed)"),
    tenantname: str = Query(..., description="tenantname"),
    service=Depends(lambda: tenant_service),
) -> Response[TenantRegisterResponseModel]:
    """
    Register a new tenant account using email, password, and name.
    """
    tenant: Tenant = await service.register_tenant(email, password, tenantname )
    return ResponseCode.OK.to_response(
        data=TenantRegisterResponseModel(
            id=tenant.id,
            name=tenant.name,
            email=tenant.email,
            is_active=tenant.is_active
        )
    )

@router.post(
    "/login",
    summary="Login an existing tenant",
    response_model=Response[TenantLoginResponseModel],
)
async def login_user_by_username(
    tenantname: str = Query(..., description="Tenant name"),
    password: str = Query(..., description="Tenant password"),
    service=Depends(lambda: tenant_service),
) -> Response[TenantLoginResponseModel]:
    """
    Authenticate a user and (optionally) return an access token.
    """
    tenant: Tenant = await service.login_tenant_by_tenantname(tenantname, password)
    return ResponseCode.OK.to_response(
        data=TenantLoginResponseModel(
            id=tenant.id,
            username=tenant.name,
            email=tenant.email,
            is_active=tenant.is_active
        )
    )