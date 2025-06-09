from typing import Any, Dict, Tuple

import httpx
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class GithubSearchComponent(RagnarokComponent):
    DESCRIPTION: str = "Search on Github"
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
            ComponentOutputTypeOption(
                name="urls",
                type=ComponentIOType.STRING_LIST,
            ),
        )

    @classmethod
    async def execute(cls, keyword: str, top_n: int) -> Dict[str, Any]:
        try:
            url = (
                "https://api.github.com/search/repositories?q="
                + keyword
                + "&sort=stars&order=desc&per_page="
                + str(top_n)
            )
            headers = {"Content-Type": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
            # response = requests.get(url=url, headers=headers).json()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                github_res = [
                    {
                        "content": '<a href="'
                        + i["html_url"]
                        + '">'
                        + i["name"]
                        + "</a>"
                        + str(i["description"])
                        + "\n stars:"
                        + str(i["watchers"])
                    }
                    for i in response.json()["items"]
                ]
                urls = [i["html_url"] for i in response.json()["items"]]
        except Exception:
            return {"content": [], "urls": []}

        if not github_res:
            return {"content": [], "urls": []}
        return {"content": github_res, "urls": urls}
