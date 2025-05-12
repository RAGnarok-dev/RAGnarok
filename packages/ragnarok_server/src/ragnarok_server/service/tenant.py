# ragnarok_server/service/tenant.py


from ragnarok_server.rdb.repositories.tenant import TenantRepository
from ragnarok_server.rdb.models import Tenant
from ragnarok_server.exceptions import DuplicateEntryError, NoResultFoundError


class TenantService:
    """
    Service for handling Tenant-related business logic.
    """
    
    def __init__(self, repo: TenantRepository = TenantRepository()):
        self.repo = repo
        
    async def register_tenant(
        self, email: str, password: str, tenantname: str, 
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

    async def login_tenant_by_tenantname(self, tenantname: str, password: str) -> Tenant:
        tenant = self.repo.get_tenant_by_tenantname(tenantname)

        if not tenant:
            raise NoResultFoundError("The user does not exist")

        return await self.repo.authenticate(
            tenantname=tenantname,
            password=password,
        )

tenant_service = TenantService()
         