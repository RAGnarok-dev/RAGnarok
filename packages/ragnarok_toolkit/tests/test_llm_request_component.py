import os

import pytest
from dotenv import load_dotenv
from ragnarok_toolkit.llm_request_component import (
    LLMIntentRecognitionComponent,
    LLMRequestComponent,
)

load_dotenv()


@pytest.mark.asyncio
async def test_llm():
    valid = LLMRequestComponent.validate()
    assert valid

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("base_url")
    model = "gpt-4o"
    message = "What's the weather today?"
    temperature = 0.0
    top_p = 0.1
    intents = {"0": "检索百科", "1": "查询天气", "2": "进行创作"}

    llm_return_intent = await LLMIntentRecognitionComponent.execute(
        api_key, base_url, temperature, top_p, model, intents, message
    )
    print(llm_return_intent)

    llm_response = await LLMRequestComponent.execute(api_key, base_url, temperature, top_p, model, message)
    print(llm_response)
