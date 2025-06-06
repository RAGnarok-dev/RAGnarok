import logging

from ragnarok_server.rdb.models import Permission
from ragnarok_server.rdb.repositories.permission import PermissionRepository

logger = logging.getLogger(__name__)

LevelMapping = {"read": 1, "write": 2, "admin": 3}


class PermissionService:
    permission_repo: PermissionRepository

    def __init__(self) -> None:
        self.permission_repo = PermissionRepository()

    async def check_permission(
        self, principal_id: int, principal_type: str, knowledge_base_id: int, permission_type: str
    ) -> bool:
        permission = await self.get_permission(principal_id, principal_type, knowledge_base_id)
        if permission is None:
            return False
        return LevelMapping[permission.permission_type] >= LevelMapping[permission_type]

    async def create_or_update_permission(self, permission: Permission) -> Permission:
        return await self.permission_repo.create_or_update_permission(permission)

    async def delete_permission(
        self, principal_id: int, principal_type: str, knowledge_base_id: int
    ) -> bool:
        return await self.permission_repo.delete_permission(
            principal_id, principal_type, knowledge_base_id
        )

    async def get_permission(self, principal_id: int, principal_type: str, knowledge_base_id: int) -> Permission:
        return await self.permission_repo.get_permission(principal_id, principal_type, knowledge_base_id)

    async def change_permission(self, knowledge_base_id: int, principal_id: int, principal_type: str,
                                permission_type: str) -> bool:
        return await self.permission_repo.change_permission(
            knowledge_base_id, principal_id, principal_type, permission_type
        )


permission_service = PermissionService()
