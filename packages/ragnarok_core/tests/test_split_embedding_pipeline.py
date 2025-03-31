import pytest
from ragnarok_core.components.official_components.text_split_component import (
    text_split_component,
)
from ragnarok_core.components.official_components.embedding_component import (
    embedding_component,
)
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode

async def test_split_embedding_pipeline():
    connection1 = PipelineNode.NodeConnection(
        from_node_id="1",
        to_node_id="2",
        from_node_output_name="embedding_component_output",
        to_node_input_name="text_split_component_input",
    )

    node1 = PipelineNode(node_id="1", component=text_split_component, forward_node_info=(connection1,))
    node2 = PipelineNode(node_id="2", component=embedding_component, forward_node_info=(), output_name="embeddings")

    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
        },
        {
            "outer_input": ("1", ".\test_document.pdf"),
        },
    )
    print("\n\n")
    async for output in pipeline.run_async(outer_input="outer input"):
        print(output)