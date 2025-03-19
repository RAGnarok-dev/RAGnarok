import asyncio
from typing import Any, Dict, Optional, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class TestComponent1(RagnarokComponent):
    DESCRIPTION: str = "description 1"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="component1_input_1",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="component1_input_2",
                allowed_types={ComponentIOType.INT, ComponentIOType.STRING},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="component1_output_1", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="component1_output_2", type=ComponentIOType.INT),
        )

    @classmethod
    def execute(cls, component1_input_1: str, component1_input_2: Optional[int | str]) -> Dict[str, Any]:
        return {"component1_output_1": component1_input_1 + str(component1_input_2), "component1_output_2": 7777777}


class TestComponent2(RagnarokComponent):
    DESCRIPTION: str = "description 2"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="component2_input_1",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="component2_output_1", type=ComponentIOType.INT),)

    @classmethod
    async def execute(cls, component2_input_1: Optional[str]) -> Dict[str, int]:
        await asyncio.sleep(1)
        if component2_input_1 is None:
            return {"component2_output_1": 0}
        return {"component2_output_1": len(component2_input_1)}


class TestComponent3(RagnarokComponent):
    DESCRIPTION: str = "description 3"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(name="component3_input_1", allowed_types={ComponentIOType.STRING}, required=True),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="component3_output_1", type=ComponentIOType.STRING),)

    @classmethod
    def execute(cls, component3_input_1: str) -> Dict[str, str]:
        return {"component3_output_1": "this is res of component 3"}
