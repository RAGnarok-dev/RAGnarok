import asyncio
from typing import Any, Optional

import pytest
from ragnarok_toolkit.common import PermissionType, PrincipalType
from ragnarok_toolkit.permission import PermissionManager

test_manager = PermissionManager()


@pytest.mark.asyncio
async def test_cache():
    time = 0

    async def fake_handler(
        sender: Any, principal_type: PrincipalType, principal_id: int, knowledge_base_id: int
    ) -> Optional[PermissionType]:
        nonlocal time
        await asyncio.sleep(2)
        time += 1
        return None if time % 2 == 0 else PermissionType.ADMIN

    test_manager.register_permission_require_handler(fake_handler)

    assert await test_manager.check_permission(PrincipalType.USER, 1, 1, PermissionType.WRITE)
    # should also be True, because of cache
    assert await test_manager.check_permission(PrincipalType.USER, 1, 1, PermissionType.ADMIN)
