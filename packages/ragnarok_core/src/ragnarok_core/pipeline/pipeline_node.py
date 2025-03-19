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
        # each node in one pipeline has a unique id
        self.node_id = node_id
        # execution component
        self.component = component
        # key in the pipeline output dict. set None if not a output node
        self.output_name = output_name
        # trigger nodes
        self.forward_node_info = forward_node_info
        # input data, originally None
        self.input_data = {
            param: None for param in [input_option["name"] for input_option in component.input_options()]
        }
        # num of the unprepared input data
        self.waiting_num = len(component.input_options())
