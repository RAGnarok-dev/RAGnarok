# tests/test_weather_pipeline.py
import pytest

from ragnarok_core.components.official_components.custom_mcp_server_component  import CustomMCPServerComponent
from ragnarok_core.components.official_components.mcp_stdio_component          import make_stdio_mcp_component
from ragnarok_core.pipeline.pipeline_node                import PipelineNode
from ragnarok_core.pipeline.pipeline_entity              import PipelineEntity

# ----------------------------------------------------------------------
WEATHER_SERVER_CODE = """\
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather", log_level="ERROR")

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
    return f\"\"\"\
Event: {props.get('event', 'Unknown')}
Area:  {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
\"\"\"

@mcp.tool()
async def get_alerts(state: str) -> str:
    url = f\"{NWS_API_BASE}/alerts/active/area/{state}\"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."
    return "\\n---\\n".join(format_alert(f) for f in data["features"])

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    points = await make_nws_request(f\"{NWS_API_BASE}/points/{latitude},{longitude}\")
    if not points:
        return "Unable to fetch forecast data for this location."
    forecast_url = points["properties"]["forecast"]
    forecast = await make_nws_request(forecast_url)
    if not forecast:
        return "Unable to fetch detailed forecast."
    periods = forecast["properties"]["periods"]
    return "\\n---\\n".join(
        f\"{p['name']}: {p['temperature']}°{p['temperatureUnit']} – {p['detailedForecast']}\"
        for p in periods[:3]
    )

if __name__ == "__main__":
    mcp.run(transport='stdio')
"""

# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_weather_forecast_pipeline():
    # NodeConnection：server 的 cmd → forecast 的 cmd
    conn_cmd = PipelineNode.NodeConnection(
        from_node_id="server",
        to_node_id="forecast",
        from_node_output_name="cmd",
        to_node_input_name="cmd",
    )

    # Node A：启动 MCP server，并把 conn_cmd 挂到 forward_node_info
    node_server = PipelineNode(
        node_id="server",
        component=CustomMCPServerComponent,
        forward_node_info=(conn_cmd,),  
        output_name="server_res"
    )

    # Node B：调用 get_forecast
    ForecastComp = make_stdio_mcp_component("get_forecast")
    node_forecast = PipelineNode(
        node_id="forecast",
        component=ForecastComp,
        forward_node_info=(),
        output_name="forecast_res",
    )

    pipeline = PipelineEntity(
        {
            "server":   node_server,
            "forecast": node_forecast,
        },
        {
            "server_name": ("server", "server_name"),
            "server_code": ("server", "server_code"),
            "dependencies": ("server", "dependencies"),
            "latitude":   ("forecast", "latitude"),
            "longitude":  ("forecast", "longitude"),
            "port":      ("server", "port"),
        },              
    )

    async for out in pipeline.run_async(
        server_name="weather_test",
        server_code=WEATHER_SERVER_CODE,
        dependencies="httpx mcp[cli] fastmcp",
        latitude=40.7128, 
        longitude=-74.006,  
    ):
        print(out)
