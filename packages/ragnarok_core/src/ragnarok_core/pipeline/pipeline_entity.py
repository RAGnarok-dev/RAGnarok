import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Literal

from ragnarok_core.pipeline.pipeline_node import PipelineNode


@dataclass
class ProcessingResult:
    type: Literal["process_info", "output_info"]
    data: Dict[str, Any]


class PipelineEntity:
    def __init__(self, node_map: Dict[str, PipelineNode]) -> None:
        self.node_map = node_map
        self.begin_nodes: List[PipelineNode] = []
        for node in node_map.values():
            if len(node.component.input_options()) == 0:
                self.begin_nodes.append(node)
        # TODO consider set a global pool
        # self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(node_map))

    # def run_node_sync(self, node: PipelineNode) -> Generator[ProcessingResult, None, None]:
    #     """run a node execution function, purely sync version"""
    #
    #     # TODO is it necessary to perform parameter verification here?
    #     node_outputs = node.component.execute(**node.input_data)
    #
    #     # return current node result
    #     yield ProcessingResult("process_info", node_outputs)
    #
    #     # if is output node, yield output info
    #     if node.output_name is not None:
    #         yield ProcessingResult("output_info", {node.output_name: node_outputs})
    #
    #     # trigger forward nodes
    #     futures = []
    #     for connection in node.forward_node_info:
    #         current_output = node_outputs[connection.from_node_output_name]
    #         trigger_node = self.node_map[connection.to_node_id]
    #         trigger_node.input_data[connection.to_node_input_name] = current_output
    #         trigger_node.waiting_num -= 1
    #         if trigger_node.waiting_num == 0:
    #             future = self.thread_pool.submit(self.run_node_sync, trigger_node)
    #             futures.append(future)
    #
    #     for future in concurrent.futures.as_completed(futures):
    #         result_generator = future.result()
    #         yield from result_generator

    async def run_async(self) -> AsyncGenerator[ProcessingResult, None]:
        # TODO generator and coroutine bug
        tasks = []
        for node in self.begin_nodes:
            task = asyncio.create_task(self.run_node_async(node))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for result_generator in results:
            async for result in result_generator:
                yield result

    async def run_node_async(self, node: PipelineNode) -> AsyncGenerator[ProcessingResult, None]:
        """run a node execution function, async version"""

        if asyncio.iscoroutinefunction(node.component.execute):
            node_outputs = await node.component.execute(**node.input_data)
        else:
            node_outputs = node.component.execute(**node.input_data)

        # return current node result
        yield ProcessingResult("process_info", node_outputs)

        # if is output node, yield output info
        if node.output_name is not None:
            yield ProcessingResult("output_info", {node.output_name: node_outputs})

        # trigger forward nodes
        tasks = []
        for connection in node.forward_node_info:
            current_output = node_outputs[connection.from_node_output_name]
            trigger_node = self.node_map[connection.to_node_id]
            trigger_node.input_data[connection.to_node_input_name] = current_output
            trigger_node.waiting_num -= 1
            if trigger_node.waiting_num == 0:
                task = asyncio.create_task(self.run_node_async(trigger_node))
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks)
            for result_generator in results:
                async for result in result_generator:
                    yield result
