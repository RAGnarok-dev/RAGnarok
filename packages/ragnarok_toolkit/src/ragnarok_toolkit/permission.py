import logging
from collections.abc import Callable
from typing import Any, Coroutine, Tuple

from blinker import NamedSignal, signal
from cachetools import LRUCache
from ragnarok_toolkit.config import PERMISSION_CACHE_SIZE

logger = logging.getLogger(__name__)


class PermissionManager:
    def __init__(self) -> None:
        # cache the permission, (access_token, knowledge_base_id) -> true / false. str type
        self.permission_cache: LRUCache[Tuple[str, str], bool] = LRUCache(maxsize=PERMISSION_CACHE_SIZE)
        # the signal to require a permission
        self.require_permission_signal: NamedSignal = signal("require_permission")

    def register_permission_require_handler(
        self, handler: Callable[[Any, str, str], Coroutine[Any, Any, bool]]
    ) -> None:
        """register handler of permission requirement signal, async version"""
        self.require_permission_signal.connect(handler)

    async def check_permission(self, access_token: str, knowledge_base_id: str) -> bool:
        """check a certain permission"""
        try:
            # 1. check cache
            if p := self.permission_cache.get((access_token, knowledge_base_id)):
                return p

            # 2. request for upper layer, send signal
            results = await self.require_permission_signal.send_async(
                self,
                access_token=access_token,
                knowledge_base_id=knowledge_base_id,
            )

            new_perm = results[-1][1]

            # update cache
            self.permission_cache[(access_token, knowledge_base_id)] = new_perm
            return new_perm
        except Exception as e:
            # downgrade to False if error occurs
            logger.error("[check_permission] error:", e)
            return False
