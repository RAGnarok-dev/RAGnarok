import asyncio
from ragnarok_core.components.official_components.mcp_stdio_component import SessionContextManager

async def test_session():
    cmd = ["python", "echo_server.py"]  # 假设你的 echo MCP server 这样启动
    tool_name = "echo"

    async with SessionContextManager(cmd, tool_name) as (sess, tool):
        print("Tool loaded:", tool.name)

        res = await sess.call_tool(name="echo", arguments={"text": "hello world"})
        print("Tool response:", res.content)

if __name__ == "__main__":
    asyncio.run(test_session())
