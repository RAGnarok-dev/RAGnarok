import pytest
from ragnarok_server.rdb.engine import init_rdb
from ragnarok_server.rdb.models import LLMSession
from ragnarok_server.rdb.repositories.llm_session import LLMSessionRepository
from ragnarok_server.rdb.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_llm_session():
    await init_rdb()
    user_repo = UserRepository()

    user = await user_repo.get_user_by_username("alex")
    if user is None:
        user = await user_repo.create_user("alex", "aa@bb.cc", "abcdef#")
        assert user.id != 0
    print(user, user.id)

    await LLMSessionRepository.delete_all_sessions()
    llm_sessions = await LLMSessionRepository.get_sessions_by_creator(f"user-{user.id}")
    if len(llm_sessions) == 0:
        print("creating new session")
        llm_session_1 = LLMSession(
            title="a session for questions",
            created_by=f"user-{user.id}",
            history={"messages": []},
        )
        llm_session_1 = await LLMSessionRepository.create_session(llm_session_1)
    else:
        llm_session_1 = llm_sessions[0]
    assert llm_session_1

    new_history = {
        "messages": [
            {"role": "user", "content": "What the weather in Hangzhou?"},
            {
                "role": "assistant",
                "content": """
                 根据杭州市气象台的公告，从今天起，连续五天的平均气温将高于22℃，标志着夏季的到来。
                 今日天气晴朗，最高气温预计达到31°C，最低气温约为18°C，风力较弱，空气湿度适中，适合户外活动。
                 不过，紫外线强度较高，建议外出时注意防晒和补水。未来几天，杭州将持续高温天气。
                 5月13日（周二）天气多云转晴，最高气温预计为32°C，最低气温约为20°C；5月14日（周三）晴转多云，最高气温可能升至33°C，最低气温约为23°C。
                 然而，从5月15日（周四）开始，云量将增多，局部地区可能出现阵雨，气温略有下降。预计5月16日（周五）将有中雨，最高气温约为27°C，最低气温约为21°C。
                 """,
            },
        ]
    }
    print("old history:", llm_session_1.history)
    res = await LLMSessionRepository.update_dialog_history(llm_session_1.id, new_history)
    assert res
    llm_session_1 = await LLMSessionRepository.get_session_by_id(llm_session_1.id)
    assert llm_session_1
    print("new history:", llm_session_1.history)
