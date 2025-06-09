import logging
from typing import Optional

from passlib.context import CryptContext
from pydantic import EmailStr
from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Tenant, User
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(Tenant).where(Tenant.name == tenantname)
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tenant_by_email(self, email: EmailStr) -> Optional[Tenant]:
        """
        Fetch a Tenant by email.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(Tenant).where(Tenant.email == email)
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """
        Fetch a Tenant by id.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_tenant(
        self,
        tenantname: str,
        email: EmailStr,
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

    async def authenticate(
        self, tenantname: Optional[str] = None, email: Optional[EmailStr] = None, password: str = ""
    ) -> Optional[Tenant]:
        """
        Validate credentials using either tenantname or email. Returns the Tenant if successful, else None.
        """
        if not tenantname and not email:
            logger.debug("Authentication failed: no identifier (tenantname/email) provided.")
            return None

        tenant = None
        if tenantname:
            tenant = await self.get_tenant_by_tenantname(tenantname)
        elif email:
            tenant = await self.get_tenant_by_email(email)

        if not tenant:
            logger.debug("Authentication failed: tenant not found.")
            return None

        if not pwd_context.verify(password, tenant.password_hash):
            logger.debug("Authentication failed: invalid password.")
            return None

        return tenant

    async def invite_user_to_tenant(self, tenant_id: int, user_email: str) -> Optional[User]:
        """
        Invite a user to join a tenant. This sets the user's tenant_id if the user exists.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(User).where(User.email == user_email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"Invite failed: user with email={user_email} not found.")
                return None

            user.tenant_id = tenant_id
            await session.commit()
            await session.refresh(user)

            logger.info(f"User {user.username} (email={user.email}) is now part of tenant id={tenant_id}")
        return user

    async def remove_user_from_tenant(self, tenant_id: int, user_email: str) -> Optional[User]:
        """
        Remove a user from a tenant by clearing their tenant_id.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(User).where(User.email == user_email, User.tenant_id == tenant_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"Remove failed: user with email={user_email} not found in tenant {tenant_id}")
                return None

            user.tenant_id = None
            await session.commit()
            await session.refresh(user)

            logger.info(f"User {user.username} (email={user.email}) removed from tenant id={tenant_id}")
        return user

    async def get_all_users_info(self, tenant_id: int) -> list[User]:
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(User).where(User.tenant_id == tenant_id)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return list(users)

    async def update_tenant_avatar(self, tenant_id: int, new_avatar_url: str, new_name: str) -> Tenant:
        async with self._session_factory() as session:  # type: AsyncSession
            stmt_check = select(Tenant).where(Tenant.name == new_name, Tenant.id != tenant_id)
            result = await session.execute(stmt_check)
            existing_tenant = result.scalar_one_or_none()
            if not existing_tenant:
                stmt = update(Tenant).where(Tenant.id == tenant_id).values(avatar_url=new_avatar_url, name=new_name).returning(Tenant)
                result = await session.execute(stmt)
                await session.commit()
                return result.scalar_one_or_none()
            else:
                stmt = select(Tenant).where(Tenant.id == tenant_id)
                result = await session.execute(stmt)
                await session.commit()
                return result.scalar_one_or_none()

    async def change_password(self, tenant_id: int, new_password: str) -> Tenant:
        async with self._session_factory() as session:
            stmt = update(Tenant).where(Tenant.id == tenant_id).values(password_hash=new_password).returning(Tenant)
            result = await session.execute(stmt)
            await session.commit()
            return result.scalar_one_or_none()
