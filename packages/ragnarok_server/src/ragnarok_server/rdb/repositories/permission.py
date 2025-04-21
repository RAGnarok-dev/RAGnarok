# ragnarok_server/rdb/repository/permission.py

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragnarok_server.rdb.models import (
    Permission,
    PermissionType,
    PrincipalType,
)
from ragnarok_server.auth import decode_access_token  # your JWT decoding function
from ragnarok_server.rdb.engine import get_async_session  # your AsyncSession factory

logger = logging.getLogger(__name__)


class PermissionRepository:
    """
    DAL for the Permission table.
    Implements RBAC lookup based on (principal_id, principal_type) from JWT.
    """

    def __init__(self, session_factory=get_async_session):
        self._session_factory = session_factory

    async def has_permission(
        self,
        principal_id: int,
        principal_type: PrincipalType,
        kb_id: int,
        action: PermissionType,
    ) -> bool:
        """
        Check whether the given principal (user or tenant) has `action`
        on knowledge base `kb_id`.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = (
                select(Permission)
                .where(
                    Permission.principal_id == principal_id,
                    Permission.principal_type == principal_type,
                    Permission.knowledge_base_id == kb_id,
                    Permission.permission_type == action,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def permission_handler(
        self,
        sender: Any,
        *,
        access_token: str,
        knowledge_base_id: str,
        action: str,
    ) -> bool:
        """
        Signal handler to plug into PermissionManager.
        - Decode JWT to get principal_id and principal_type
        - Call has_permission(...)
        """
        try:
            payload = decode_access_token(access_token)
            # assume payload.principal_id: int, payload.principal_type: "user"|"tenant"
            principal_id = payload.principal_id
            principal_type = PrincipalType(payload.principal_type)
            kb_id = int(knowledge_base_id)
            perm_action = PermissionType(action)
        except Exception as e:
            logger.warning("permission_handler: failed to decode token or parse params", exc_info=e)
            return False

        try:
            return await self.has_permission(principal_id, principal_type, kb_id, perm_action)
        except Exception as e:
            logger.error("permission_handler: DB query failed", exc_info=e)
            return False
