import pytest
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode
from ragnarok_core.components.official_components.text_split_component import TextSplitComponent
from ragnarok_core.components.official_components.embedding_component import EmbeddingComponent  # 请替换为实际的模块路径


@pytest.mark.asyncio
async def test_pipeline_execution():
    print("1111111111111111111111111111")
    # # 定义连接
    connection1 = PipelineNode.NodeConnection(
        from_node_id="1",
        to_node_id="2",
        from_node_output_name="text_chunks",
        to_node_input_name="sentences",
    )

    # 定义节点
    node1 = PipelineNode(
        node_id="1",
        component=TextSplitComponent,
        forward_node_info=(connection1,),
        output_name="text_chunks"
    )

    node2 = PipelineNode(
        node_id="2",
        component=EmbeddingComponent,
        forward_node_info=(),
        output_name="embeddings"
    )

    # 构建 Pipeline
    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
        },
        {
            "outer_input": ("1", "pdf_path"),
        },
    )

    # 运行 Pipeline
    pdf_test_path = "test_document.pdf"  # 替换为实际 PDF 文件路径
    print(pdf_test_path, "\n\n")
    async for output in pipeline.run_async(outer_input=pdf_test_path):
        print(output)
