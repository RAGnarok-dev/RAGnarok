import pytest
from ragnarok_core.components.official_components.crawler_component import (
    CrawlerComponent,
)


@pytest.mark.asyncio
async def test_crawler():
    url = (
        "http://www.baidu.com/link?url=gI-W2MRe8nv7v-zVvH-71"
        "TroD5Dohcr20j9mcLOsK1WH0Q6APr37O80WTdYQF3ArCabRrHsw114qWC8FrMZzxK"
    )
    res = await CrawlerComponent.execute(url)
    print(res)
