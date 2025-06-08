import re
from typing import Any, Dict, Tuple

import httpx
from bs4 import BeautifulSoup
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class BaiduSearchComponent(RagnarokComponent):
    DESCRIPTION: str = "Search on Baidu"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="keyword",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="top_n",
                allowed_types={ComponentIOType.INT},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="content",
                type=ComponentIOType.STRING_LIST,
            ),
        )

    @classmethod
    async def execute(cls, keyword: str, top_n: int) -> Dict[str, Any]:
        url = "https://www.baidu.com/s?wd=" + keyword + "&rn=" + str(top_n)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                url_res = []
                title_res = []
                body_res = []
                for item in soup.select(".result.c-container"):
                    # extract title
                    title_res.append(item.select_one("h3 a").get_text(strip=True))
                    url_res.append(item.select_one("h3 a")["href"])
                    body_res.append(
                        item.select_one(".c-abstract").get_text(strip=True) if item.select_one(".c-abstract") else ""
                    )
                baidu_res = [
                    {"content": re.sub("<em>|</em>", "", '<a href="' + url + '">' + title + "</a>    " + body)}
                    for url, title, body in zip(url_res, title_res, body_res)
                ]
                return {"content": baidu_res}
            return {"content": ""}

        except Exception:
            return {"content": ""}
