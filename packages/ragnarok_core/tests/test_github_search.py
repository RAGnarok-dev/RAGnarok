import pytest
from ragnarok_core.components.official_components.github_search_component import (
    GithubSearchComponent,
)


@pytest.mark.asyncio
async def test_github_search():
    keyword = "GeeCeeCee"
    top_n = 10
    res = await GithubSearchComponent.execute(keyword=keyword, top_n=top_n)
    print(res)
    assert len(res["content"]) <= top_n
