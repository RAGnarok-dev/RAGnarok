import os
import asyncio
import casbin
from sqlalchemy.future import select
from ragnarok_server.rdb.base import AsyncSessionLocal
from ragnarok_server.rdb.permission import Permission, PermissionType
from ragnarok_toolkit.permission import PermissionManager

# Get the directory of the current file (permissions.py)
this_dir = os.path.dirname(os.path.realpath(__file__))
# Build the absolute path for the rbac_model.conf file
model_path = os.path.join(this_dir, "rbac_model.conf")

# Initialize Casbin Enforcer with the RBAC model using the absolute path
enforcer = casbin.Enforcer(model_path, adapter=None)
enforcer.clear_policy()  # Clear policies to load fresh data


async def load_permissions_from_db():
    """Load permission records from the DB and set up Casbin policies."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Permission))
        permissions = result.scalars().all()
        for perm in permissions:
            uid = str(perm.user_id)
            kb_id = str(perm.knowledge_base_id)
            perm_type = perm.permission_type.value  # 'read', 'write', or 'admin'
            if perm_type == "admin":
                enforcer.add_grouping_policy(uid, f"kb_{kb_id}_admin")
            elif perm_type == "write":
                enforcer.add_grouping_policy(uid, f"kb_{kb_id}_writer")
            elif perm_type == "read":
                enforcer.add_grouping_policy(uid, f"kb_{kb_id}_reader")
        # For each knowledge base, add policy rules so that each role has its permissions
        kb_ids = {perm.knowledge_base_id for perm in permissions}
        for kb_id in kb_ids:
            obj = str(kb_id)
            enforcer.add_policy(f"kb_{obj}_reader", obj, "read")
            enforcer.add_policy(f"kb_{obj}_writer", obj, "read")
            enforcer.add_policy(f"kb_{obj}_writer", obj, "write")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "read")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "write")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "admin")


async def require_permission(user, knowledge_base, action: str) -> bool:
    """
    Check if the user has the required permission on the knowledge base.
    If the user is the tenant admin and the KB belongs to the same tenant, allow directly.
    Otherwise, use Casbin enforcement.
    """
    # If user is tenant admin and KB is in the same tenant, allow immediately.
    if user.is_tenant_admin and knowledge_base.tenant_id == user.tenant_id:
        return True
    sub = str(user.id)
    obj = str(knowledge_base.id)
    return enforcer.enforce(sub, obj, action)


# Create a global PermissionManager instance
permission_manager = PermissionManager()

# Register the require_permission function as the permission check handler.
# Note: The expected signature is (access_token: str, knowledge_base_id: str) -> bool.
# If needed, you can wrap or adapt require_permission accordingly.
permission_manager.register_permission_require_handler(require_permission)


async def init_permission_system():
    """Initialize the permission system by loading DB data into Casbin."""
    await load_permissions_from_db()
