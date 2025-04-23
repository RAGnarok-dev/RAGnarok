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
        from_node_id="3",
        to_node_id="1",
        from_node_output_name="component3_output_1",
        to_node_input_name="component1_input_1",
    )
    connection2 = PipelineNode.NodeConnection(
        from_node_id="3",
        to_node_id="2",
        from_node_output_name="component3_output_1",
        to_node_input_name="component2_input_1",
    )
    connection3 = PipelineNode.NodeConnection(
        from_node_id="2",
        to_node_id="1",
        from_node_output_name="component2_output_1",
        to_node_input_name="component1_input_2",
    )
    node1 = PipelineNode(node_id="1", component=TestComponent1, forward_node_info=(), output_name="node1_res")
    node2 = PipelineNode(node_id="2", component=TestComponent2, forward_node_info=(connection3,))
    node3 = PipelineNode(node_id="3", component=TestComponent3, forward_node_info=(connection1, connection2))
    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
            "3": node3,
        },
        {
            "outer_input": ("3", "component3_input_1"),
        },
    )
    print("\n\n")
    async for output in pipeline.run_async(outer_input="outer input"):
        print(output)


def test_convertion():
    connection1 = PipelineNode.NodeConnection(
        from_node_id="3",
        to_node_id="1",
        from_node_output_name="component3_output_1",
        to_node_input_name="component1_input_1",
    )
    connection2 = PipelineNode.NodeConnection(
        from_node_id="3",
        to_node_id="2",
        from_node_output_name="component3_output_1",
        to_node_input_name="component2_input_1",
    )
    connection3 = PipelineNode.NodeConnection(
        from_node_id="2",
        to_node_id="1",
        from_node_output_name="component2_output_1",
        to_node_input_name="component1_input_2",
    )
    node1 = PipelineNode(node_id="1", component=TestComponent1, forward_node_info=(), output_name="node1_res")
    node2 = PipelineNode(node_id="2", component=TestComponent2, forward_node_info=(connection3,))
    node3 = PipelineNode(node_id="3", component=TestComponent3, forward_node_info=(connection1, connection2))
    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
            "3": node3,
        },
        {
            "outer_input": ("3", "component3_input_1"),
        },
    )
    print(pipeline.to_json_str())
