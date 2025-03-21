import os

from ragnarok_toolkit.llm_request_component import LLMRequestComponent


def test_llm():
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = "https://vip.DMXapi.com/v1/"
    model = "gpt-4o"
    llm_response = LLMRequestComponent.execute(
        api_key, base_url, model, "search on the internet and retrieve information about BUAA"
    )

    print(llm_response)


if __name__ == "__main__":
    test_llm()
