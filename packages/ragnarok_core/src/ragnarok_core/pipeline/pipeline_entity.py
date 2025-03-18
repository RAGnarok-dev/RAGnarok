import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Literal

from ragnarok_core.pipeline.pipeline_node import PipelineNode


@dataclass
class PipelineExecutionInfo:
    node_id: str
    type: Literal["process_info", "output_info"]
    timestamp: datetime
    data: Dict[str, Any] = None  # auto set by __post_init__

    def __post_init__(self):
        self.timestamp = datetime.now()


class PipelineEntity:
    def __init__(self, node_map: Dict[str, PipelineNode]) -> None:
        # store the mapping of the node_id and node entity
        self.node_map = node_map
        # begging nodes, with no input
        self.begin_nodes = [node for node in node_map.values() if len(node.component.input_options()) == 0]
        # store the processing result, breaking the contagiousness of multi async generator
        self.result_queue: asyncio.Queue[PipelineExecutionInfo] = asyncio.Queue(maxsize=2 * len(self.begin_nodes))
        # num of the unfinished node
        self.remaining_num = len(node_map)

    async def run_async(self) -> AsyncGenerator[PipelineExecutionInfo, None]:
        for node in self.begin_nodes:
            asyncio.create_task(self.run_node_async(node))

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
