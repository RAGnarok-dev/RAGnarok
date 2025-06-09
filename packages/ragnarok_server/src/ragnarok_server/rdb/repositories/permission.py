# ragnarok_server/rdb/repository/permission.py

import logging
from typing import Dict
from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Permission
from sqlalchemy import delete, select, update

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

    @classmethod
    async def change_permission(cls, knowledge_base_id: int, principal_id: int, principal_type: str, permission_type: str) -> bool:
        async with get_async_session() as session:
            stmt = update(Permission).where(
                Permission.knowledge_base_id == knowledge_base_id,
                Permission.principal_id == principal_id,
                Permission.principal_type == principal_type).values(permission_type=permission_type)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_all_knowledge_bases_by_id(cls, principal_id: int, principal_type: str) -> Dict[int, str]:
        async with get_async_session() as session:
            stmt = select(Permission.knowledge_base_id, Permission.permission_type).where(
                Permission.principal_id == principal_id,
                Permission.principal_type == principal_type)
            result = await session.execute(stmt)
            rows = result.all()
            return {kb_id: perm for kb_id, perm in rows}

    async def get_permission_list(self, knowledge_base_id: int) -> list[Permission]:
        async with get_async_session() as session:
            stmt = select(Permission).where(Permission.knowledge_base_id == knowledge_base_id)
            result = await session.execute(stmt)
            permissions = result.scalars().all()
            return permissions


