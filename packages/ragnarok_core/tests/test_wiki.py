from ragnarok_core.components.official_components.wikipedia_search_coponent import (
    WikipediaSearchComponent,
)


def test_wiki_search():
    keyword = "Ragnarok"
    top_n = 5
    res = WikipediaSearchComponent.execute(keyword=keyword, top_n=top_n)
    print(res)
    assert len(res["content"]) <= top_n
