import os
import sys

import pytest
from dotenv import load_dotenv

from ragnarok_core.components.official_components.llm_request_component import (
    LLMIntentRecognitionComponent,
    LLMRequestComponent,
)

load_dotenv()

@pytest.mark.asyncio
async def test_llm():
    assert LLMRequestComponent.validate() 
    assert LLMIntentRecognitionComponent.validate()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("base_url")
    print(base_url)
    model = "gemini-2.5-flash-preview-04-17"
    question = "What's the weather today?"
    temperature = 0.6
    top_p = 0.9
    intents = {"0": "检索百科", "1": "查询天气", "2": "进行创作"}

    llm_return_intent = await LLMIntentRecognitionComponent.execute(
        question, intents, model, api_key, base_url, temperature, top_p, 
    )
    print(llm_return_intent)


    question = "What's the date today?"
    content_list = [
        "今天北京的天气以多云为主，最高气温为29°C，最低气温为16°C。气温较为温暖，但部分地区可能存在空气质量不佳的情况，建议在户外活动时注意防护。目前风力较弱，全天降雨的可能性不大。",
        "上海今天阳光明媚，气温较高，最高温达到32°C，最低气温为18°C。天空大多晴朗，适合进行各种户外活动。市区风力轻微，空气较为干燥，总体天气舒适宜人。",
        "深圳位于中国南部，今日天气以晴朗为主，最高气温为31°C，最低气温为21°C。全天预计维持晴好状态，微风轻拂，降雨可能性较低。温暖的气温和阳光明媚的天气为市民外出或休闲活动提供了理想条件。"
    ]

    history = {
            "messages": [
                {"role": "user", "content": "What the weather in Hangzhou?"},
                {"role": "assistant", "content": """
                 根据杭州市气象台的公告，从今天起，连续五天的平均气温将高于22℃，标志着夏季的到来。
                 今日天气晴朗，最高气温预计达到31°C，最低气温约为18°C，风力较弱，空气湿度适中，适合户外活动。
                 不过，紫外线强度较高，建议外出时注意防晒和补水。未来几天，杭州将持续高温天气。
                 5月13日（周二）天气多云转晴，最高气温预计为32°C，最低气温约为20°C；5月14日（周三）晴转多云，最高气温可能升至33°C，最低气温约为23°C。
                 然而，从5月15日（周四）开始，云量将增多，局部地区可能出现阵雨，气温略有下降。预计5月16日（周五）将有中雨，最高气温约为27°C，最低气温约为21°C。 
                 """},
            ]
        }
    llm_response = await LLMRequestComponent.execute(question,  content_list, history, model, api_key, base_url, temperature, top_p)
    print(llm_response)
