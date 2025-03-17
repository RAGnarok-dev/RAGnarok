import pytest
from ragnarok_core.components.official_components.test_component import (
    TestComponent1,
    TestComponent2,
    TestComponent3,
)
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode


@pytest.mark.asyncio
async def test_pipeline_execution():
    connection1 = PipelineNode.NodeConnection(
        from_node_id="3", to_node_id="1", from_node_output_name="out_from_3", to_node_input_name="param1"
    )
    connection2 = PipelineNode.NodeConnection(
        from_node_id="3", to_node_id="2", from_node_output_name="out_from_3", to_node_input_name="x1"
    )
    connection3 = PipelineNode.NodeConnection(
        from_node_id="2", to_node_id="1", from_node_output_name="out", to_node_input_name="param2"
    )
    node1 = PipelineNode(node_id="1", component=TestComponent1, forward_node_info=(), output_name="node1_res")
    node2 = PipelineNode(node_id="2", component=TestComponent2, forward_node_info=(connection3,))
    node3 = PipelineNode(node_id="3", component=TestComponent3, forward_node_info=(connection1, connection2))
    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
            "3": node3,
        }
    )

    async for output in pipeline.run_async():
        print(output)
