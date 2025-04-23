import logging
from collections.abc import Callable
from typing import Any, Coroutine, Tuple

from blinker import NamedSignal, signal
from cachetools import LRUCache
from ragnarok_toolkit.common import PermissionType, PrincipalType
from ragnarok_toolkit.config import PERMISSION_CACHE_SIZE

logger = logging.getLogger(__name__)


class PermissionManager:
    def __init__(self) -> None:
        # cache the permission, (principal_type, principal_id, knowledge_base_id) -> permission_type
        self.permission_cache: LRUCache[Tuple[PrincipalType, int, int], PermissionType] = LRUCache(
            maxsize=PERMISSION_CACHE_SIZE
        )
        # the signal to require a permission
        self.require_permission_signal: NamedSignal = signal("require_permission")

    def register_permission_require_handler(
        self, handler: Callable[[Any, PrincipalType, int, int], Coroutine[Any, Any, PermissionType | None]]
    ) -> None:
        """register handler of permission requirement signal, async version"""
        self.require_permission_signal.connect(handler)

    async def check_permission(
        self, principal_type: PrincipalType, principal_id: int, knowledge_base_id: int, permission_type: PermissionType
    ) -> bool:
        try:
            # 1. check cache
            if p := self.permission_cache.get((principal_type, principal_id, knowledge_base_id)):
                return p >= permission_type

            # 2. send signal with the additional action parameter
            results = await self.require_permission_signal.send_async(
                self,
                principal_type=principal_type,
                principal_id=principal_id,
                knowledge_base_id=knowledge_base_id,
            )
            new_perm = results[-1][1]
            if new_perm is None:
                return False

            # update cache
            self.permission_cache[(principal_type, principal_id, knowledge_base_id)] = new_perm
            return new_perm >= permission_type
        except Exception as e:
            logger.error("[check_permission] error:", e)
            return False
