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
        src = []
        if isinstance(url, list):
            for url in url:
                if url is not None and url != "":
                    src.append(url)
        else:
            if url is not None and url != "":
                src.append(url)
        if len(src) == 0:
            src.append(
                "http://www.baidu.com/link?url=VvAyOcDxOGtHkj3xo7jyUbltRk0DaiN99mn_Fi"
                "-baBykqTSNiWYx4YAV7nVXDFYfTJux2nbHJGidl3Z_mNMy6a"
            )
        res = ""
        for s in src:
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url=s, bypass_cache=True)
                res += result.markdown + "\n\n"
        return {"content": res}
