import asyncio
import os
import sys
import signal
import time
import tempfile
import subprocess
import shutil
import pytest
import requests
import json
import pytest_asyncio

from ragnarok_core.components.official_components.custom_mcp_server_component import CustomMCPServerComponent
from ragnarok_core.components.official_components.mcp_component import make_mcp_component
from ragnarok_core.components.official_components.mcp_stdio_component import make_stdio_mcp_component

CUSTOM_PORT = 3333
OFFICIAL_PORT = 3334
STDIO_CMD   = ["uvx", "mcp-server-fetch"] 

# --- 辅助测试函数 ---
def _run_fetch_test(base_url: str):
    print(f"[TEST] Running fetch test with base_url: {base_url}")
    FetchComp = make_mcp_component("fetch", base_url)
    print("[TEST] FetchComp created, executing...")

    result = FetchComp.execute(url="https://httpbin.org/get", max_length=2000)
    print("[TEST] Execution finished. Result keys:", list(result.keys()))

    content = result.get("content")
    assert isinstance(content, str), "content 应为字符串"

    data = json.loads(content)
    print("[TEST] Parsed content JSON keys:", list(data.keys()))
    assert "url" in data and data["url"].startswith("https://httpbin.org/get"), "应包含 url"
    assert "headers" in data and isinstance(data["headers"], dict), "应包含 headers"
    assert "origin" in data, "应包含 origin"
    assert "content" in result, "MCP 返回值应包含 'content' 键"

# --- 自定义内嵌服务器 Fixture ---
@pytest.fixture(scope="module")
def custom_fetch_server():
    print("[FIXTURE] Starting custom Fetch MCP server...")
    fetch_code = '''
from fastapi import FastAPI
import os, requests

app = FastAPI()

@app.get("/info")
def info():
    return {
        "tools": [{
            "name": "fetch",
            "inputs": [
                {"name": "url", "type": "string", "required": True},
                {"name": "max_length", "type": "int", "required": False}
            ],
            "outputs": [
                {"name": "content", "type": "string"}
            ]
        }]
    }

@app.post("/invoke")
def invoke(body: dict):
    args = body.get("args", {})
    resp = requests.get(args["url"])
    max_len = args.get("max_length", 1000)
    return {"content": resp.text[:max_len]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "3333"))
    uvicorn.run(app, host="0.0.0.0", port=port)
''' 
    out = CustomMCPServerComponent.execute(
        server_name="custom_fetch",
        server_code=fetch_code,
        port=CUSTOM_PORT,
        dependencies="fastapi uvicorn requests",
    )
    base_url = out["base_url"]
    pid = out["pid"]
    temp_dir = out["temp_dir"]
    print(f"[FIXTURE] Custom server running at {base_url}, pid={pid}")

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/info", timeout=1)
            print(f"[FIXTURE] /info -> {r.status_code}, {r.json()}")
            if r.status_code == 200:
                break
        except Exception as e:
            print("[FIXTURE] Waiting for custom MCP server:", str(e))
            time.sleep(0.5)
    else:
        CustomMCPServerComponent.stop(pid, temp_dir)
        pytest.skip("Custom Fetch MCP Server 未就绪")

    yield base_url
    print("[FIXTURE] Stopping custom MCP server")
    CustomMCPServerComponent.stop(pid, temp_dir)

# --- 官方 Fetch Server Fixture ---
# ------------------ 新增 STDIO 测试 ------------------
@pytest_asyncio.fixture(scope="module")
async def official_fetch_stdio():
    # 启动子进程并用 SDK 封装
    transport = await stdio_client.exec(cmd=STDIO_CMD)
    session = ClientSession(transport)
    await session.__aenter__()         # 打开会话
    yield session                      # <-- 这里 yield 的就是 ClientSession
    await session.__aexit__(None, None, None)

# --- 测试用例 ---

def test_custom_fetch_returns_valid_json(custom_fetch_server):
    print("[TEST CASE] Running test_custom_fetch_returns_valid_json")
    _run_fetch_test(custom_fetch_server)


@pytest.mark.asyncio
async def test_official_fetch_returns_valid_json_stdio(official_fetch_stdio):
    FetchComp = make_stdio_mcp_component(STDIO_CMD, "fetch")
    result = await official_fetch_stdio.call_tool(
        name="fetch",
        arguments={"url": "https://httpbin.org/get", "max_length": 2000}
    )
    text = result[0].content
    data = json.loads(text)
    assert data["url"].startswith("https://httpbin.org/get")
    assert isinstance(data["headers"], dict)
    assert "origin" in data