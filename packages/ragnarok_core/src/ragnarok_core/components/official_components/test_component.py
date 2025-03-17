from typing import Optional, Tuple

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
    def execute(cls, param1: str, param2: Optional[int]) -> Tuple[str]:
        return (param1 + str(param2),)


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
        return (ComponentOutputTypeOption(name="out", type=ComponentIOType.STRING),)

    @classmethod
    def execute(cls, x1: Optional[str]) -> Tuple[str]:
        if x1 is None:
            return ("None",)
        return (x1,)
