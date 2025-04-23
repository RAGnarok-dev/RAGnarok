from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult

mcp = FastMCP("echo_server")

@mcp.tool("echo")
async def echo_tool(text: str) -> CallToolResult:
    return CallToolResult(content=[{"text": text}])

if __name__ == "__main__":
    mcp.run(transport='stdio')
