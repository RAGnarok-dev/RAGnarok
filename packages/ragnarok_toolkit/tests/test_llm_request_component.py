import os

import pytest
from ragnarok_toolkit.llm_request_component import LLMRequestComponent


@pytest.mark.asyncio
async def test_llm():
    valid = LLMRequestComponent.validate()
    assert valid

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = "https://vip.DMXapi.com/v1/"
    model = "gpt-4o"
    message = "search on the internet and retrieve informations about BUAA"
    llm_response = await LLMRequestComponent.execute(api_key, base_url, model, message)

    print(llm_response)
