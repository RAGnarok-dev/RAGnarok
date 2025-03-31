import pytest
from ragnarok_server.permissions import require_permission, enforcer


# 定义简单的 Dummy 类，用于模拟 User 和 KnowledgeBase 对象
class DummyUser:
    def __init__(self, id, tenant_id, is_tenant_admin=False):
        self.id = id
        self.tenant_id = tenant_id
        self.is_tenant_admin = is_tenant_admin


class DummyKnowledgeBase:
    def __init__(self, id, tenant_id):
        self.id = id
        self.tenant_id = tenant_id


# 在每个测试之前清空 enforcer 的策略，确保测试环境干净
@pytest.fixture(autouse=True)
def reset_enforcer():
    enforcer.clear_policy()
    yield
    enforcer.clear_policy()


@pytest.mark.asyncio
async def test_tenant_admin_always_has_permission():
    """
    Tenant admin should always have permission regardless of policies.
    """
    user = DummyUser(id=1, tenant_id=100, is_tenant_admin=True)
    kb = DummyKnowledgeBase(id=10, tenant_id=100)
    allowed = await require_permission(user, kb, "read")
    assert allowed is True


@pytest.mark.asyncio
async def test_regular_user_without_permission():
    """
    A regular user without any assigned policy should not have permission.
    """
    user = DummyUser(id=2, tenant_id=100, is_tenant_admin=False)
    kb = DummyKnowledgeBase(id=20, tenant_id=100)
    allowed = await require_permission(user, kb, "read")
    assert allowed is False


@pytest.mark.asyncio
async def test_regular_user_with_read_permission():
    """
    Regular user with a 'read' grouping policy and policy should have permission.
    """
    user = DummyUser(id=3, tenant_id=100, is_tenant_admin=False)
    kb = DummyKnowledgeBase(id=30, tenant_id=100)
    # 手动添加该用户对应的读者角色和策略
    enforcer.add_grouping_policy(str(user.id), f"kb_{kb.id}_reader")
    enforcer.add_policy(f"kb_{kb.id}_reader", str(kb.id), "read")
    allowed = await require_permission(user, kb, "read")
    assert allowed is True


@pytest.mark.asyncio
async def test_regular_user_with_write_permission_for_read():
    """
    如果用户有写权限角色，且该角色同时允许 read，则请求 read 权限应通过。
    """
    user = DummyUser(id=4, tenant_id=100, is_tenant_admin=False)
    kb = DummyKnowledgeBase(id=40, tenant_id=100)
    # 添加写权限角色，同时写权限角色包含 read 权限
    enforcer.add_grouping_policy(str(user.id), f"kb_{kb.id}_writer")
    enforcer.add_policy(f"kb_{kb.id}_writer", str(kb.id), "read")
    enforcer.add_policy(f"kb_{kb.id}_writer", str(kb.id), "write")
    allowed = await require_permission(user, kb, "read")
    assert allowed is True


@pytest.mark.asyncio
async def test_regular_user_without_required_action():
    """
    如果用户仅有读权限，尝试写操作时应返回 False。
    """
    user = DummyUser(id=5, tenant_id=100, is_tenant_admin=False)
    kb = DummyKnowledgeBase(id=50, tenant_id=100)
    enforcer.add_grouping_policy(str(user.id), f"kb_{kb.id}_reader")
    enforcer.add_policy(f"kb_{kb.id}_reader", str(kb.id), "read")
    # 请求写权限应不通过
    allowed = await require_permission(user, kb, "write")
    assert allowed is False
