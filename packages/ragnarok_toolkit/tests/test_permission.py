import asyncio
from typing import Any

import pytest
from ragnarok_toolkit.permission import PermissionManager

test_manager = PermissionManager()


@pytest.mark.asyncio
async def test_cache():
    time = 0

    async def fake_handler(sender: Any, access_token: str, knowledge_base_id: str) -> bool:
        await asyncio.sleep(1)
        return time % 2 == 0

    test_manager.register_permission_require_handler(fake_handler)

    assert await test_manager.check_permission("1", "1")
    # should also be True, because of cache
    assert await test_manager.check_permission("1", "1")
