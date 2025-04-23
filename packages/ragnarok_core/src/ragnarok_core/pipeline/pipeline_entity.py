import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Literal, Tuple

from ragnarok_core.pipeline.pipeline_node import PipelineNode


@dataclass
class PipelineExecutionInfo:
    node_id: str
    type: Literal["process_info", "output_info"]
    data: Dict[str, Any]
    timestamp: datetime = None  # auto set by __post_init__

    def __post_init__(self):
        self.timestamp = datetime.now()


class PipelineEntity:
    def __init__(self, node_map: Dict[str, PipelineNode], inject_input_mapping: Dict[str, Tuple[str, str]]) -> None:
        # store the mapping of the node_id and node entity
        self.node_map = node_map
        # store the processing result, breaking the contagiousness of multi async generator
        self.result_queue: asyncio.Queue[PipelineExecutionInfo] = asyncio.Queue(maxsize=2 * len(self.node_map))
        # num of the unfinished node
        self.remaining_num = len(node_map)
        # outer input inject mapping. eg: inject_name -> (node_id, node_input_name)
        self.inject_input_mapping = inject_input_mapping
        # beginning nodes, whose input is either empty or totally injected
        self.begin_nodes = [
            node
            for node in node_map.values()
            if len(node.component.input_options()) == 0
            or {input_option.get("name") for input_option in node.component.input_options()}.issubset(
                {
                    node_input_name
                    for node_id, node_input_name in inject_input_mapping.values()
                    if node_id == node.node_id
                }
            )
        ]

    async def run_async(self, *args, **kwargs) -> AsyncGenerator[PipelineExecutionInfo, None]:
        """execute the pipeline, async version"""
        # 1. inject outer input
        for inject_name, (node_id, node_input_name) in self.inject_input_mapping.items():
            actual_input_value = kwargs.get(inject_name)
            # TODO check if actual_input_value is None or not correspond to node expected type
            self.node_map[node_id].input_data[node_input_name] = actual_input_value

        # 2. run beginning task
        for node in self.begin_nodes:
            asyncio.create_task(self.run_node_async(node))

        # 3. collect result
        while self.remaining_num > 0:
            execution_info = await self.result_queue.get()
            if execution_info.type == "process_info":
                self.remaining_num -= 1

            yield execution_info

    async def run_node_async(self, node: PipelineNode) -> None:
        """run a node execution function, async version"""

        # TODO error handling
        if asyncio.iscoroutinefunction(node.component.execute):
            node_outputs = await node.component.execute(**node.input_data)
        else:
            node_outputs = node.component.execute(**node.input_data)

        # if is output node, yield output info
        # HINT!: this have to be set before putting process_info, because we use process_info to count remaining num
        if node.output_name is not None:
            self.result_queue.put_nowait(
                PipelineExecutionInfo(node.node_id, "output_info", {node.output_name: node_outputs})
            )

        # return current node result
        self.result_queue.put_nowait(PipelineExecutionInfo(node.node_id, "process_info", node_outputs))

        # trigger forward nodes
        tasks = []
        for connection in node.forward_node_info:
            current_output = node_outputs[connection.from_node_output_name]
            trigger_node = self.node_map[connection.to_node_id]
            if trigger_node is None:
                continue

            trigger_node.input_data[connection.to_node_input_name] = current_output
            trigger_node.waiting_num -= 1
            if trigger_node.waiting_num == 0:
                task = asyncio.create_task(self.run_node_async(trigger_node))
                tasks.append(task)

        await asyncio.gather(*tasks)

    @classmethod
    def from_json_str(cls, json_str: str) -> "PipelineEntity":
        """instantiate a pipeline entity from a json format string"""
        pass

    def to_json_str(self) -> str:
        """convert to json format"""
        nodes: List[Dict[str, Any]] = []
        connections: List[Dict[str, str]] = []
        for node_id, pipeline_node in self.node_map.items():
            node: Dict[str, Any] = {"node_id": node_id, "component": pipeline_node.component.__name__}
            if pipeline_node.output_name is not None:
                node["output_name"] = pipeline_node.output_name
            nodes.append(node)
            for forward_node_info in pipeline_node.forward_node_info:
                connections.append(
                    {
                        "from_node_id": forward_node_info.from_node_id,
                        "from_output_name": forward_node_info.from_node_output_name,
                        "to_node_id": forward_node_info.to_node_id,
                        "to_node_input_name": forward_node_info.to_node_input_name,
                    }
                )

        res = {"nodes": nodes, "connections": connections, "inject_input_mapping": self.inject_input_mapping}
        return json.dumps(res)
