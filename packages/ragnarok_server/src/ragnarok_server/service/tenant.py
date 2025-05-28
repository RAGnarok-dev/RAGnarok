# ragnarok_server/service/tenant.py
from typing import Optional

from ragnarok_server.rdb.repositories.tenant import TenantRepository
from ragnarok_server.rdb.models import Tenant, User
from ragnarok_server.exceptions import DuplicateEntryError, NoResultFoundError, InvalidArgsError
from pydantic import EmailStr
from ragnarok_server.auth import create_access_token


class TenantService:
    """
    Service for handling Tenant-related business logic.
    """
    
    def __init__(self, repo: TenantRepository = TenantRepository()):
        self.repo = repo
        
    async def register_tenant(
        self, email: EmailStr, password: str, tenantname: str,
    ) -> Tenant:
        # 1) Check if tenantname is already taken
        if await self.repo.get_tenant_by_tenantname(tenantname):
            raise DuplicateEntryError("Tenant name already occupied")
        
        # 2) Check if email is already registered
        if await self.repo.get_tenant_by_email(email):
            raise DuplicateEntryError("Email has been registered")
         
        # 3) Create tenant
        return await self.repo.create_tenant(
            tenantname=tenantname,
            email=email,
            password=password,     
        )

    async def login_tenant(self, email: EmailStr = None, tenantname: str = None, password: str = None) -> dict:
        if not (tenantname or email):
            raise InvalidArgsError("Must provide either tenantname or email")
        if not password:
            raise InvalidArgsError("Password is required")

        tenant = None
        if tenantname:
            tenant = await self.repo.get_tenant_by_tenantname(tenantname)
        elif email:
            tenant = await self.repo.get_tenant_by_email(email)

        if not tenant:
            raise NoResultFoundError("Tenant not found")

        # # 校验密码
        # if not verify_password(password, user.password):  # 取决于你是否加密保存密码
        #     raise InvalidArgsError("Password error")

        tenant = await self.repo.authenticate(
            tenantname=tenantname,
            email=email,
            password=password,
        )
        if not tenant:
            raise InvalidArgsError("Password error")

        token = create_access_token(
            principal_id=tenant.id,
            principal_type="tenant"
        )

        return {
            "tenant": tenant,
            "access_token": token,
            "token_type": "Bearer"
        }

    @staticmethod
    async def get_tenant_info(tenant: Tenant) -> dict:
        if not tenant:
            raise InvalidArgsError("Tenant does not exist, please log in")

        return {
            "tenantname": tenant.name,
            "id": tenant.id,
            "avatar": "avatar"
        }
    async def invite_user_to_tenant(self, tenant_id: int, user_email: str) -> Optional[User]:
        """
        Invite a user to join a tenant by email.
        """
        return await self.repo.invite_user_to_tenant(tenant_id, user_email)



    async def remove_user_from_tenant(self, tenant_id: int, user_email: str) -> Optional[User]:
        """
        Remove a user from a tenant by email.
        """
        return await self.repo.remove_user_from_tenant(tenant_id, user_email)

    async def get_all_users_info(self, tenant: Tenant) -> list[User]:
        if not tenant:
            raise InvalidArgsError("Tenant does not exist, please log in")

        return await self.repo.get_all_users_info(tenant.id)


tenant_service = TenantService()


         