import pytest
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode
from ragnarok_core.components.official_components.text_split_component import TextSplitComponent
from ragnarok_core.components.official_components.embedding_component import EmbeddingComponent  # 请替换为实际的模块路径


@pytest.mark.asyncio
async def test_pipeline_execution():
    # print("1111111111111111111111111111")
    # # 定义连接
    connection1 = PipelineNode.NodeConnection(
        from_node_id="1",
        to_node_id="2",
        from_node_output_name="text_chunks",
        to_node_input_name="text_chunks",
    )

    # 定义节点
    node1 = PipelineNode(
        node_id="1",
        component=TextSplitComponent,
        forward_node_info=(connection1,),
        pos=(0,1),
        output_name="text_chunks"
    )

    node2 = PipelineNode(
        node_id="2",
        component=EmbeddingComponent,
        forward_node_info=(),
        pos=(0, 2),
        output_name="embeddings"
    )

    # 构建 Pipeline
    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
        },
        {
            "file_type": ("1", "file_type"),
            "file_byte": ("1", "file_byte"),
            "split_type": ("1", "split_type"),
        },
    )

    # 运行 Pipeline
    test_pdf_path = "test_file.txt"  # 替换为实际 PDF 文件路径
    with open(test_pdf_path, "rb") as f:
        test_file_byte = f.read()
    # print(test_pdf_path, "\n\n")
    async for output in pipeline.run_async(file_type="txt", file_byte=test_file_byte, split_type="semantic_split"):
        print(output if output.type == "output_info" else "")
