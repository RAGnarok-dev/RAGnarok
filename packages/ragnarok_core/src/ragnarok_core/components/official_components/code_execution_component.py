from typing import Any, Dict, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class CodeExecutionComponent(RagnarokComponent):
    DESCRIPTION: str = "Execute Python code"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="code",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return ()

    @classmethod
    async def execute(cls, code: str) -> Dict[str, Any]:
        try:
            exec(code)
            return {}
        except Exception as e:
            return {"error": str(e)}
