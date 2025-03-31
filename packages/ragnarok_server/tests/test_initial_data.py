# test_initial_data.py
import pytest
from sqlalchemy.future import select

# Import the async session and models
from ragnarok_server.rdb.base import AsyncSessionLocal
from ragnarok_server.rdb.tenant import Tenant
from ragnarok_server.rdb.user import User
from ragnarok_server.rdb.knowledge_base import KnowledgeBase
from ragnarok_server.rdb.permission import Permission, PermissionType


@pytest.mark.asyncio
async def test_insert_initial_data():
    # Create an async session
    async with AsyncSessionLocal() as session:
        # 1. Insert a Tenant.
        tenant = Tenant(name="TestTenant")
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        # 2. Insert the tenant admin user.
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash="hashed_password",
            tenant_id=tenant.id,
            is_tenant_admin=True
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        # Update tenant's admin_user_id to point to the admin user.
        tenant.admin_user_id = admin_user.id
        session.add(tenant)
        await session.commit()

        # 3. Insert a KnowledgeBase belonging to the tenant.
        kb = KnowledgeBase(
            title="Test KB",
            description="This is a test knowledge base.",
            tenant_id=tenant.id
        )
        session.add(kb)
        await session.commit()
        await session.refresh(kb)

        # 4. Insert a regular user in the same tenant.
        user = User(
            username="user1",
            email="user1@example.com",
            password_hash="hashed_password",
            tenant_id=tenant.id,
            is_tenant_admin=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # 5. Insert a Permission record: give the regular user READ permission on the knowledge base.
        permission = Permission(
            user_id=user.id,
            knowledge_base_id=kb.id,
            permission_type=PermissionType.READ
        )
        session.add(permission)
        await session.commit()

        # 6. Query back to validate the data
        result_tenant = await session.execute(select(Tenant).where(Tenant.id == tenant.id))
        fetched_tenant = result_tenant.scalar_one()
        assert fetched_tenant.name == "TestTenant"

        result_admin = await session.execute(select(User).where(User.id == admin_user.id))
        fetched_admin = result_admin.scalar_one()
        assert fetched_admin.is_tenant_admin is True

        result_kb = await session.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb.id))
        fetched_kb = result_kb.scalar_one()
        assert fetched_kb.title == "Test KB"

        result_perm = await session.execute(select(Permission).where(Permission.user_id == user.id))
        fetched_perm = result_perm.scalar_one()
        assert fetched_perm.permission_type == PermissionType.READ
