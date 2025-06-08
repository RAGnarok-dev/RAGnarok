import pytest
from ragnarok_core.components.official_components.code_execution_component import (
    CodeExecutionComponent,
)


@pytest.mark.asyncio
async def test_code_execution():
    code = """print("hello world")"""
    _ = await CodeExecutionComponent.execute(code)
