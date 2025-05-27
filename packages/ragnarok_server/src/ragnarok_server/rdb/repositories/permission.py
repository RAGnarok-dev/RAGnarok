# ragnarok_server/rdb/repository/permission.py

import logging

from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Permission
from sqlalchemy import delete, select

logger = logging.getLogger(__name__)


class PermissionRepository:
    @classmethod
    async def create_or_update_permission(cls, permission: Permission) -> Permission:
        async with get_async_session() as session:
            stmt = select(Permission).where(
                Permission.principal_id == permission.principal_id,
                Permission.principal_type == permission.principal_type,
                Permission.knowledge_base_id == permission.knowledge_base_id,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                session.add(permission)
            else:
                session.merge(permission)
            return permission

    @classmethod
    async def delete_permission(cls, principal_id: int, principal_type: str, knowledge_base_id: int) -> bool:
        async with get_async_session() as session:
            stmt = delete(Permission).where(
                Permission.principal_id == principal_id,
                Permission.principal_type == principal_type,
                Permission.knowledge_base_id == knowledge_base_id,
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_permission(cls, principal_id: int, principal_type: str, knowledge_base_id: int) -> Permission:
        async with get_async_session() as session:
            stmt = select(Permission).where(
                Permission.principal_id == principal_id,
                Permission.principal_type == principal_type,
                Permission.knowledge_base_id == knowledge_base_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
