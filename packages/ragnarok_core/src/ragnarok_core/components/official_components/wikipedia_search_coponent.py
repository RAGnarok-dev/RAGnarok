from typing import Any, Dict, Tuple

import wikipedia
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class WikipediaSearchComponent(RagnarokComponent):

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
    def execute(cls, keyword: str, top_n: int) -> Dict[str, Any]:
        top_n = int(top_n)
        try:
            wiki_res = []
            urls = []
            wikipedia.set_lang("zh")
            wiki_engine = wikipedia
            for wiki_key in wiki_engine.search(keyword, results=top_n):
                page = wiki_engine.page(title=wiki_key, auto_suggest=False)
                wiki_res.append({"content": '<a href="' + page.url + '">' + page.title + "</a> " + page.summary})
                urls.append(page.url)
        except Exception:
            return {"content": [], "urls": []}

        if not wiki_res:
            return {"content": [], "urls": []}
        return {"content": wiki_res, "urls": urls}
