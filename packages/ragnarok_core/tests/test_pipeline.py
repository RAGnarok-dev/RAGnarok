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
    async for output in pipeline.run_async(outer_input="outer_input"):
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
    node1 = PipelineNode(
        node_id="1", component=TestComponent1, forward_node_info=(), output_name="node1_res", pos={"x": 1.1, "y": 1.2}
    )
    node2 = PipelineNode(
        node_id="2", component=TestComponent2, forward_node_info=(connection3,), pos={"x": 1.1, "y": 1.2}
    )
    node3 = PipelineNode(
        node_id="3", component=TestComponent3, forward_node_info=(connection1, connection2), pos={"x": 1.1, "y": 1.2}
    )
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


def test_from_json_str():
    # 准备测试用的JSON字符串
    test_json = """
    {
        "nodes": [
            {
                "node_id": "1",
                "component": "TestComponent1",
                "position": {
                    "x": 1.1,
                    "y": 1.2
                },
                "output_name": "node1_res"
            },
            {
                "node_id": "2",
                "component": "TestComponent2",
                "position": {
                    "x": 1.1,
                    "y": 1.2
                }
            },
            {
                "node_id": "3",
                "component": "TestComponent3",
                "position": {
                    "x": 1.1,
                    "y": 1.2
                }
            }
        ],
        "connections": [
            {
                "from_node_id": "2",
                "from_output_name": "component2_output_1",
                "to_node_id": "1",
                "to_node_input_name": "component1_input_2"
            },
            {
                "from_node_id": "3",
                "from_output_name": "component3_output_1",
                "to_node_id": "1",
                "to_node_input_name": "component1_input_1"
            },
            {
                "from_node_id": "3",
                "from_output_name": "component3_output_1",
                "to_node_id": "2",
                "to_node_input_name": "component2_input_1"
            }
        ],
        "inject_input_mapping": {
            "outer_input": [
                "3",
                "component3_input_1"
            ]
        }
    }
    """

    pipeline = PipelineEntity.from_json_str(test_json)
    assert isinstance(pipeline, PipelineEntity)
    assert len(pipeline.node_map) == 3
    assert pipeline.inject_input_mapping["outer_input"] == ["3", "component3_input_1"]

    # invalid_json = '{"nodes": [], "connections": []}'
    # with pytest.raises(ValueError):
    #     PipelineEntity.from_json_str(invalid_json)
    #
    # with pytest.raises(ValueError):
    #     PipelineEntity.from_json_str("invalid json string")
