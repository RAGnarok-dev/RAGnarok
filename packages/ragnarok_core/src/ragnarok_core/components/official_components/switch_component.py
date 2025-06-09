import asyncio
import json
from typing import Any, Dict, Tuple

from ragnarok_core.components import component_manager
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class SwitchComponent(RagnarokComponent):
    """
    Component class for selecting and executing a component based on an enum value
    """

    DESCRIPTION: str = "Execute a component based on enum value"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="enum_value",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="component_mapping",
                allowed_types={ComponentIOType.DICT},
                required=True,
            ),
            ComponentInputTypeOption(
                name="input_params",
                allowed_types={ComponentIOType.DICT},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="result", type=ComponentIOType.DICT),)

    @classmethod
    async def execute(
        cls,
        enum_value: str,
        component_mapping: dict,  # Mapping from enum values to component names
        input_params: dict,  # Input parameters
    ) -> Dict[str, Any]:
        if isinstance(input_params, str):
            input_params = json.loads(input_params)
        if isinstance(component_mapping, dict):
            component_mapping = component_mapping.copy()
        """
        Execute the component function

        Parameters:
        - enum_value: Enum value used to select the component to execute
        - component_mapping: Mapping from enum values to component names, e.g.
            {"1": "TestComponent1", "2": "TestComponent2"}
        - input_params: Input parameters to pass to the selected component

        Returns:
        - Execution result of the selected component
        """

        # Check if enum value is in the mapping
        if enum_value not in component_mapping:
            return {"result": {"error": f"Enum value {enum_value} not found in component mapping"}}

        # Get the component name to execute
        component_name = component_mapping[enum_value]

        # Get the component from the component manager
        component_info = component_manager.get_component_by_name(component_name)
        if component_info is None:
            return {"result": {"error": f"Component {component_name} not found"}}

        # Get the component class
        component_class = component_info.component_class

        try:
            # Execute the component
            if asyncio.iscoroutinefunction(component_class.execute):
                # Async execution
                result = await component_class.execute(**input_params)
            else:
                # Sync execution
                result = component_class.execute(**input_params)

            return {"result": result}
        except Exception as e:
            return {"result": {"error": f"Error executing component {component_name}: {str(e)}"}}
