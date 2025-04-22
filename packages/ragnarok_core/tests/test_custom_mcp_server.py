# tests/test_weather_stdio_integration.py
import os
import sys
import time
import pytest, pytest_asyncio

from ragnarok_core.components.official_components.custom_mcp_server_component import CustomMCPServerComponent
from ragnarok_core.components.official_components.mcp_stdio_component import make_stdio_mcp_component

# 复制你的完整 weather 服务代码
WEATHER_SERVER_CODE = """\
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather", log_level="ERROR")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f\"\"\"
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
\"\"\"

@mcp.tool()
async def get_alerts(state: str) -> str:
    url = f\"{NWS_API_BASE}/alerts/active/area/{state}\"
    data = await make_nws_request(url)
    if not data or \"features\" not in data:
        return \"Unable to fetch alerts or no alerts found.\"
    if not data[\"features\"]:
        return \"No active alerts for this state.\"
    return \"\\n---\\n\".join(format_alert(f) for f in data[\"features\"])

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    points = await make_nws_request(f\"{NWS_API_BASE}/points/{latitude},{longitude}\")
    if not points:
        return \"Unable to fetch forecast data for this location.\"
    forecast_url = points[\"properties\"][\"forecast\"]
    forecast = await make_nws_request(forecast_url)
    if not forecast:
        return \"Unable to fetch detailed forecast.\"
    periods = forecast[\"properties\"][\"periods\"]
    return \"\\n---\\n\".join(
        f\"{p['name']}: {p['temperature']}°{p['temperatureUnit']} – {p['detailedForecast']}\" 
        for p in periods[:3]
    )

if __name__ == \"__main__\":
    mcp.run(transport='stdio')
"""

@pytest.fixture(scope="module")
def weather_server():
    # 启动 stdio MCP 服务，组件内部会创建 venv 并跑 server.py（使用 stdio）
    result = CustomMCPServerComponent.execute(
        server_name="weather_test",
        server_code=WEATHER_SERVER_CODE,
        dependencies="httpx mcp[cli] fastmcp"
        # dependencies="httpx mcp-server-fastmcp"运行测试时那份代码会被你的主环境
    )
    # 从 temp_dir 拼出 venv 下的 python 可执行文件路径
    bin_dir = os.path.join(
        result["temp_dir"],
        "venv",
        "Scripts" if os.name == "nt" else "bin"
    )
    python_exec = os.path.join(bin_dir, "python")
    script_path = os.path.join(result["temp_dir"], "server.py")
    cmd = [python_exec, script_path]

    # 给一下启动缓冲
    time.sleep(10)
    yield result, cmd

    # Teardown：停止 MCP 服务 并清理临时文件夹
    CustomMCPServerComponent.stop(result["pid"], result["temp_dir"])

@pytest_asyncio.fixture(scope="function")
async def alerts_comp(weather_server):
    _, cmd = weather_server
    Wrapper = make_stdio_mcp_component(cmd=cmd, tool_name="get_alerts")
    return Wrapper

@pytest_asyncio.fixture(scope="function")
async def forecast_comp(weather_server):
    _, cmd = weather_server
    Wrapper = make_stdio_mcp_component(cmd=cmd, tool_name="get_forecast")
    return Wrapper

@pytest.mark.asyncio
async def test_get_alerts_invalid_state(alerts_comp):
    await alerts_comp._ensure()
    res = await alerts_comp.execute(state="ZZ")
    assert "Unable to fetch alerts" in res.output["text"]
    

@pytest.mark.asyncio
async def test_get_forecast_invalid_location(forecast_comp):
    await forecast_comp._ensure()
    res = await forecast_comp.execute(latitude=999.0, longitude=999.0)
    assert "forecast" in res.output["text"]
