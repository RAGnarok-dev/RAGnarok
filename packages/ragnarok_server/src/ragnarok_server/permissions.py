import os
import asyncio
import casbin
import hashlib
from sqlalchemy.future import select

from ragnarok_server.rdb import APIKey
from ragnarok_server.rdb.base import AsyncSessionLocal
from ragnarok_server.rdb.user import User
from ragnarok_server.rdb.knowledge_base import KnowledgeBase
from ragnarok_server.rdb.permission import Permission, PermissionType
from ragnarok_toolkit.permission import PermissionManager

# --- API Key Authentication Configuration ---
# In this implementation, we do not use JWT.
# Instead, the client provides an API key (plaintext), and we compute its SHA-256 hash.
# The API key record is stored in the database with only the hash value.
# The APIKey generation process (in your CRUD endpoints) should generate a random key,
# compute its hash, and store only the hash.

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

def _hash_key(plaintext: str) -> str:
    """
    Compute the SHA-256 hash of the given plaintext API key and return its hex digest.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

async def get_user_by_apikey(api_key: str) -> User:
    """
    Retrieve the User object associated with the given API key.
    The API key is provided in plaintext; we compute its hash and query the database.
    Raises an Exception if the API key is invalid or disabled.
    """
    key_hash = _hash_key(api_key)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Permission).select_from(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.enabled == True
            )
        )
        # Alternatively, query directly from APIKey table:
        result = await session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.enabled == True)
        )
        api_key_record = result.scalar_one_or_none()
        if not api_key_record:
            raise Exception("Invalid or disabled API key")
        result = await session.execute(select(User).where(User.id == api_key_record.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise Exception("User not found")
        return user

async def get_kb_by_id(knowledge_base_id: str) -> KnowledgeBase:
    """
    Retrieve the KnowledgeBase object by its ID from the database.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        kb = result.scalar_one_or_none()
        if not kb:
            raise Exception("KnowledgeBase not found")
        return kb

async def permission_check_adapter(sender, api_key: str, knowledge_base_id: str, action: str) -> bool:
    """
    Adapter function for PermissionManager.
    Converts the provided API key and knowledge_base_id into User and KnowledgeBase objects,
    then checks the required permission using require_permission.
    The 'action' parameter can be "read", "write", or "admin".
    """
    user = await get_user_by_apikey(api_key)
    kb = await get_kb_by_id(knowledge_base_id)
    return await require_permission(user, kb, action)

# --- Initialize PermissionManager ---
permission_manager = PermissionManager()
# Register the adapter function with the expected signature:
# (api_key: str, knowledge_base_id: str, action: str) -> bool.
permission_manager.register_permission_require_handler(permission_check_adapter)

async def init_permission_system():
    """
    Initialize the permission system by loading database permission data into Casbin.
    This function should be called during application startup.
    """
    await load_permissions_from_db()
