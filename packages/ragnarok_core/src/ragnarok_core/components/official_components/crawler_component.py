from typing import Any, Dict, Tuple

from crawl4ai import AsyncWebCrawler
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class CrawlerComponent(RagnarokComponent):
    DESCRIPTION = "crawler on web with given url"
    ENABLE_HINT_CHECK = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (ComponentInputTypeOption(name="url", allowed_types={ComponentIOType.STRING}, required=True),)

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="content",
                type=ComponentIOType.STRING,
            ),
        )

    @classmethod
    async def execute(cls, url: str) -> Dict[str, Any]:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url, bypass_cache=True)
            return {"content": result.markdown}
