import logging
from typing import Optional

from passlib.context import CryptContext
from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Tenant
from sqlalchemy import select

logger = logging.getLogger(__name__)

# configure your password hashing context (must match how you created password_hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TenantRepository:
    """
    Repository for Tenant authentication and lookup.
    """

    def __init__(self, session_factory=get_async_session):
        self._session_factory = session_factory
        
    async def get_tenant_by_tenantname(self, tenantname: str) -> Optional[Tenant]:
        """
        Fetch a Tenant by tenantname.
        """
        async with self._session_factory() as session: # type: AsyncSession
            stmt = select(Tenant).where(Tenant.name == tenantname)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
    async def get_tenant_by_email(self, email: str) -> Optional[Tenant]:
        """
        Fetch a Tenant by email.
        """
        async with self._session_factory() as session:
            stmt = select(Tenant).where(Tenant.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
    async def create_tenant(
        self, 
        tenantname: str, 
        email: str, 
        password: str,
    ) -> Tenant:
        """
        Create a new tenant with hashed password.
        """
        password_hash = pwd_context.hash(password)
        tenant = Tenant(
            name=tenantname,
            email=email,
            password_hash=password_hash,
            is_active=True,
        )
        async with self._session_factory() as session:
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            logger.info(f"Created new tenant {tenantname!r}(id={tenant.id})")
            return tenant

    async def authenticate(self, tenantname: str, password: str) -> Optional[Tenant]:
        """
        Validate credentials. Returns the Tenant if successful, else None.
        """
        tenant = await self.get_tenant_by_tenantname(tenantname)
        if not tenant:
            logger.debug(f"Authentication failed: tenant {tenantname!r} not found.")
            return None

        if not pwd_context.verify(password, tenant.password_hash):
            logger.debug(f"Authentication failed: invalid password for {tenantname!r}.")
            return None

        return tenant

