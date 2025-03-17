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
                name="param1",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="param2",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    def execute(cls, param1: str, param2: Optional[int]) -> Dict[str, Any]:
        return {"param1": param1, "param2": param2}


class TestComponent2(RagnarokComponent):
    DESCRIPTION: str = "description 2"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="x1",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.INT),)

    @classmethod
    def execute(cls, x1: Optional[str]) -> Dict[str, int]:
        if x1 is None:
            return {"out": 0}
        return {"out": len(x1)}


class TestComponent3(RagnarokComponent):
    DESCRIPTION: str = "description 3"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return ()

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="out_from_3", type=ComponentIOType.STRING),)

    @classmethod
    def execute(cls) -> Dict[str, str]:
        return {"out_from_3": "this is res of component 3"}
