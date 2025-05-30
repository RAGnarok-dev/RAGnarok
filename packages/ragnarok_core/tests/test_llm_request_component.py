import os

import pytest
from dotenv import load_dotenv
from ragnarok_core.components.official_components.llm_request_component import (
    LLMIntentRecognitionComponent,
    LLMRequestComponent,
)
from ragnarok_server.rdb.engine import init_rdb
from ragnarok_server.rdb.repositories.llm_session import LLMSessionRepository
from ragnarok_server.rdb.repositories.user import UserRepository

load_dotenv()


@pytest.mark.asyncio
async def test_llm():
    assert LLMRequestComponent.validate()
    assert LLMIntentRecognitionComponent.validate()

    await init_rdb()
    user_repo = UserRepository()
    await LLMSessionRepository.delete_all_sessions()
    user = await user_repo.get_user_by_username("alex")
    if user is None:
        user = await user_repo.create_user("alex", "aa@bb.cc", "abcdef#")
        assert user.id != 0
    print(user, user.id)

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("base_url")
    print(base_url)
    model = "gemini-2.5-flash-preview-04-17"
    question = "What's the weather today?"
    temperature = 0.6
    top_p = 0.9

    intents = {"0": "检索百科", "1": "查询天气", "2": "进行创作"}
    llm_return_intent = await LLMIntentRecognitionComponent.execute(
        question, intents, model, api_key, base_url, 3, temperature, top_p,
    )
    print(llm_return_intent)

    question = "今天北京什么天气？"
    content_list = [
        "今天北京的天气以多云为主，最高气温为29°C，最低气温为16°C。气温较为温暖，但部分地区可能存在空气质量不佳的情况，建议在户外活动时注意防护。目前风力较弱，全天降雨的可能性不大。",
        # "上海今天阳光明媚，气温较高，最高温达到32°C，最低气温为18°C。天空大多晴朗，适合进行各种户外活动。市区风力轻微，空气较为干燥，总体天气舒适宜人。",
        "深圳位于中国南部，今日天气以晴朗为主，最高气温为31°C，最低气温为21°C。全天预计维持晴好状态，微风轻拂，降雨可能性较低。温暖的气温和阳光明媚的天气为市民外出或休闲活动提供了理想条件。",
    ]

    creator_id = f"user-{user.id}"
    llm_response = await LLMRequestComponent.execute(
        creator_id, None, question, content_list, model, api_key, base_url, 3, temperature, top_p
    )
    print(llm_response)

    llm_session_id = llm_response["llm_session_id"]
    question = "今天上海和深圳的气温多少？"
    llm_response = await LLMRequestComponent.execute(
        creator_id,
        llm_session_id,
        question,
        ["最新消息，上海今天最高气温为3000°C，最低气温为-273.15°C"],
        model,
        api_key,
        base_url,
        3, 
        temperature,
        top_p,
    )
    print(llm_response)
