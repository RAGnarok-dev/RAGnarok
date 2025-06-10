import pytest
from ragnarok_core.components.official_components.baidu_search_component import (
    BaiduSearchComponent,
)
from ragnarok_core.components.official_components.crawler_component import (
    CrawlerComponent,
)
from ragnarok_core.components.official_components.llm_keyword_extract_component import (
    KeywordExtractComponent,
)
from ragnarok_core.components.official_components.str_component import StrComponent
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode

text = PipelineNode(node_id="1", component=StrComponent, forward_node_info=())
keyword_extract = PipelineNode(node_id="2", component=KeywordExtractComponent, forward_node_info=())
top_n = PipelineNode(node_id="3", component=StrComponent, forward_node_info=())
model_name = PipelineNode(node_id="4", component=StrComponent, forward_node_info=())
api_key = PipelineNode(node_id="5", component=StrComponent, forward_node_info=())
base_url = PipelineNode(node_id="6", component=StrComponent, forward_node_info=())
baidu_search = PipelineNode(node_id="7", component=BaiduSearchComponent, forward_node_info=())
crawler = PipelineNode(node_id="8", component=CrawlerComponent, forward_node_info=())

connection1 = PipelineNode.NodeConnection(
    from_node_id=text.node_id,
    to_node_id=keyword_extract.node_id,
    from_node_output_name="output",
    to_node_input_name="query",
)

connection2 = PipelineNode.NodeConnection(
    from_node_id=top_n.node_id,
    to_node_id=keyword_extract.node_id,
    from_node_output_name="output",
    to_node_input_name="size",
)

connection3 = PipelineNode.NodeConnection(
    from_node_id=model_name.node_id,
    to_node_id=keyword_extract.node_id,
    from_node_output_name="output",
    to_node_input_name="model_name",
)

connection4 = PipelineNode.NodeConnection(
    from_node_id=api_key.node_id,
    to_node_id=keyword_extract.node_id,
    from_node_output_name="output",
    to_node_input_name="api_key",
)

connection5 = PipelineNode.NodeConnection(
    from_node_id=base_url.node_id,
    to_node_id=keyword_extract.node_id,
    from_node_output_name="output",
    to_node_input_name="base_url",
)

connection6 = PipelineNode.NodeConnection(
    from_node_id=keyword_extract.node_id,
    to_node_id=baidu_search.node_id,
    from_node_output_name="keywords",
    to_node_input_name="keyword",
)

connection7 = PipelineNode.NodeConnection(
    from_node_id=top_n.node_id,
    to_node_id=baidu_search.node_id,
    from_node_output_name="output",
    to_node_input_name="top_n",
)

connection8 = PipelineNode.NodeConnection(
    from_node_id=baidu_search.node_id,
    to_node_id=crawler.node_id,
    from_node_output_name="urls",
    to_node_input_name="url",
)

text.forward_node_info = (connection1,)
top_n.forward_node_info = (connection2, connection7)
model_name.forward_node_info = (connection3,)
api_key.forward_node_info = (connection4,)
base_url.forward_node_info = (connection5,)
keyword_extract.forward_node_info = (connection6,)
baidu_search.forward_node_info = (connection8,)


pipeline = PipelineEntity(
    {
        "1": text,
        "2": keyword_extract,
        "3": top_n,
        "4": model_name,
        "5": api_key,
        "6": base_url,
        "7": baidu_search,
        "8": crawler,
    },
    {
        "text": ("1", "input"),
        "top_n": ("3", "input"),
        "model_name": ("4", "input"),
        "api_key": ("5", "input"),
        "base_url": ("6", "input"),
    },
)


@pytest.mark.asyncio
async def test_run():
    async for output in pipeline.run_async(
        text="中国近现代史",
        top_n=3,
        model_name="ernie-4.0-8k-latest",
        api_key="bce-v3/ALTAK-10eERkCqoq1ATeaEqP97Y/e404385e0d40baee64accda4a801b16ff0647d95",
        base_url="https://qianfan.baidubce.com/v2",
    ):
        print(output)
