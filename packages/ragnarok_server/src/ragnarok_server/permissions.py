import os
import asyncio
import casbin
import jwt
from jwt import PyJWTError
from sqlalchemy.future import select

from ragnarok_server.rdb.base import AsyncSessionLocal
from ragnarok_server.rdb.user import User
from ragnarok_server.rdb.knowledge_base import KnowledgeBase
from ragnarok_server.rdb.permission import Permission, PermissionType
from ragnarok_toolkit.permission import PermissionManager

# --- JWT Configuration ---
# TODO：need .env
JWT_SECRET = "your_jwt_secret"
JWT_ALGORITHM = "HS256"

# --- Casbin Model Loading ---
# Get the current file directory and construct the absolute path for rbac_model.conf.
this_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(this_dir, "rbac_model.conf")

# Initialize Casbin Enforcer with the RBAC model using the absolute path.
enforcer = casbin.Enforcer(model_path, adapter=None)
enforcer.clear_policy()  # Clear any existing policies.


async def load_permissions_from_db():
    """
    Load permission records from the database and set up Casbin policies.
    Based on the Permission table data, add grouping policies for each user,
    and add policy rules for each knowledge base.
    """
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
        # For each knowledge base, add policy rules so that each role has corresponding permissions.
        kb_ids = {perm.knowledge_base_id for perm in permissions}
        for kb_id in kb_ids:
            obj = str(kb_id)
            enforcer.add_policy(f"kb_{obj}_reader", obj, "read")
            enforcer.add_policy(f"kb_{obj}_writer", obj, "read")
            enforcer.add_policy(f"kb_{obj}_writer", obj, "write")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "read")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "write")
            enforcer.add_policy(f"kb_{obj}_admin", obj, "admin")


async def require_permission(user: User, knowledge_base: KnowledgeBase, action: str) -> bool:
    """
    Check if the user has the required permission on the knowledge base.
    If the user is a tenant admin and the knowledge base belongs to the same tenant,
    allow access directly; otherwise, enforce permission via Casbin.
    """
    if user.is_tenant_admin and knowledge_base.tenant_id == user.tenant_id:
        return True
    sub = str(user.id)
    obj = str(knowledge_base.id)
    return enforcer.enforce(sub, obj, action)


# --- JWT and Database Object Conversion Functions ---

async def get_user_by_token(access_token: str) -> User:
    """
    Decode the JWT token and retrieve the corresponding User object from the database.
    Assumes the JWT contains a "user_id" field.
    TODO: Enhance JWT validation and error handling per project requirements.
    """
    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise Exception("Token payload does not contain user_id")
    except PyJWTError as e:
        raise Exception("Invalid JWT token") from e

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise Exception("User not found")
        return user


async def get_kb_by_id(knowledge_base_id: str) -> KnowledgeBase:
    """
    Retrieve the KnowledgeBase object by its ID from the database.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id))
        kb = result.scalar_one_or_none()
        if kb is None:
            raise Exception("KnowledgeBase not found")
        return kb


async def permission_check_adapter(sender, access_token: str, knowledge_base_id: str, action: str) -> bool:
    """
    Adapter function for PermissionManager.
    Converts access_token and knowledge_base_id into User and KnowledgeBase objects,
    then checks the required permission using require_permission.
    The 'action' parameter can be "read", "write", or "admin".
    """
    user = await get_user_by_token(access_token)
    kb = await get_kb_by_id(knowledge_base_id)
    return await require_permission(user, kb, action)


# --- Initialize PermissionManager ---
permission_manager = PermissionManager()
# Register the adapter function with the expected signature:
# (access_token: str, knowledge_base_id: str, action: str) -> bool.
permission_manager.register_permission_require_handler(permission_check_adapter)


async def init_permission_system():
    """
    Initialize the permission system by loading database permission data into Casbin.
    This function should be called during application startup.
    """
    await load_permissions_from_db()
