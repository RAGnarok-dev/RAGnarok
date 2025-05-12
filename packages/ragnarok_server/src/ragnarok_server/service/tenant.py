# ragnarok_server/service/tenant.py


from ragnarok_server.rdb.repositories.tenant import TenantRepository
from ragnarok_server.rdb.models import Tenant
from ragnarok_server.exceptions import DuplicateEntryError, NoResultFoundError, InvalidArgsError
from pydantic import EmailStr



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

    async def login_tenant(self, email: EmailStr = None, tenantname: str = None, password: str = None) -> Tenant:
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

        return await self.repo.authenticate(
            tenantname=tenantname,
            email=email,
            password=password,
        )


tenant_service = TenantService()


         