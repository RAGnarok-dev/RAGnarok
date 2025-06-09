import pytest
from ragnarok_core.components.official_components.baidu_search_component import (
    BaiduSearchComponent,
)


@pytest.mark.asyncio
async def test_baidu_search():
    keyword = "软件工程"
    top_n = 5
    res = await BaiduSearchComponent.execute(keyword, top_n)
    print(res)
    assert len(res["content"]) <= top_n
