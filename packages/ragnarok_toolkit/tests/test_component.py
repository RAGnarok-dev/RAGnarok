from typing import Any, Dict, Optional, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class TestComponent1(RagnarokComponent):
    DESCRIPTION: str = "description"
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
        return {"out": param1 + str(param2)}


def test_component_validation():
    valid = TestComponent1.validate()
    assert valid
