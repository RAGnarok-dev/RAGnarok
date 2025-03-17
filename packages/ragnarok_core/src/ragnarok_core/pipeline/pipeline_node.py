from dataclasses import dataclass
from typing import Optional, Tuple, Type

from ragnarok_toolkit.component import RagnarokComponent


class PipelineNode:
    """pipeline node structured metadata"""

    @dataclass
    class NodeConnection:
        """encapsulate the forward node info"""

        from_node_id: str
        from_node_output_name: str
        to_node_id: str
        to_node_input_name: str

    def __init__(
        self,
        *,
        node_id: str,
        component: Type[RagnarokComponent],
        forward_node_info: Tuple[NodeConnection, ...],
        output_name: Optional[str] = None,
    ) -> None:
        self.node_id = node_id  # each node in one pipeline has a unique id
        self.component = component  # execution component
        self.output_name = output_name  # key in the pipeline output dict. set None if not a output node
        self.is_begin = True if len(component.input_options()) == 0 else False  # beginning node
        self.forward_node_info = forward_node_info  # trigger nodes
        self.input_data = {
            param: None for param in [input_option["name"] for input_option in component.input_options()]
        }  # input data, originally None
        self.waiting_num = len(component.input_options())  # num of the unprepared input data
