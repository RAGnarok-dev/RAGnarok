from typing import Any, Dict, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class StrComponent(RagnarokComponent):
    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="input",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="output",
                type=ComponentIOType.STRING,
            ),
        )

    @classmethod
    def execute(cls, input: str) -> Dict[str, Any]:
        return {"output": input}
