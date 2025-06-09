import pytest
from ragnarok_core.components.official_components.switch_component import (
    SwitchComponent,
)


@pytest.mark.asyncio
async def test_switch_component_selects_correct_component():
    # Test case 1: Select MockComponentA
    enum_value_a = "component_a"
    component_mapping_a = {"component_a": "MockComponentA", "component_b": "MockComponentB"}
    input_params_a = {"value": 10, "multiplier": 2}

    result_a = await SwitchComponent.execute(enum_value_a, component_mapping_a, input_params_a)
    assert result_a["result"] == {"result": 20}  # 10 * 2

    # Test case 2: Select MockComponentB
    enum_value_b = "component_b"
    component_mapping_b = {"component_a": "MockComponentA", "component_b": "MockComponentB"}
    input_params_b = {"value": 10, "multiplier": 2}

    result_b = await SwitchComponent.execute(enum_value_b, component_mapping_b, input_params_b)
    assert result_b["result"] == {"result": 12}  # 10 + 2


@pytest.mark.asyncio
async def test_switch_component_handles_missing_enum_value():
    enum_value = "non_existent_component"
    component_mapping = {"component_a": "MockComponentA"}
    input_params = {"value": 5}

    result = await SwitchComponent.execute(enum_value, component_mapping, input_params)
    assert "error" in result["result"]
    assert "not found in component mapping" in result["result"]["error"]
