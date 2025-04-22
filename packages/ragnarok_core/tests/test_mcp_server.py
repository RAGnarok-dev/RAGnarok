import os
import signal
import time
import pytest
import requests
import json

# 根据你的项目结构，修改下面两行的 import 路径
from ragnarok_core.components.official_components.custom_mcp_server_component import CustomMCPServerComponent
from ragnarok_core.components.official_components.mcp_component import make_mcp_component

FETCH_PORT = 3333

@pytest.fixture(scope="module")
def fetch_server():
    """
    启动一个本地的 Fetch MCP Server，用于后续测试。
    """
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

    # 启动 MCP Server
    out = CustomMCPServerComponent.execute(server_code=fetch_code, port=FETCH_PORT)
    base_url, pid = out["base_url"], out["pid"]

    # 等待 /info 可用
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/info", timeout=1)
            if r.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.5)
    else:
        os.kill(pid, signal.SIGTERM)
        pytest.skip("Fetch MCP Server 未就绪")

    yield base_url

    # 测试结束后停止服务器
    os.kill(pid, signal.SIGTERM)


def test_fetch_returns_valid_json(fetch_server):
    """
    使用 fetch 节点获取 httpbin 的 /get 接口，解析返回的 JSON 并验证字段。
    """
    # 将远端 Fetch MCP Server 包装为组件
    FetchComp = make_mcp_component("fetch", fetch_server)

    # 调用 httpbin.org/get，限制长度
    result = FetchComp.execute(url="https://httpbin.org/get", max_length=2000)

    # 拿到原始字符串
    content = result.get("content")
    assert isinstance(content, str), "content 应为字符串"

    # 尝试解析 JSON
    data = json.loads(content)

    # 验证返回结构中包含 'url'、'headers' 等字段
    assert "url" in data and data["url"].startswith("https://httpbin.org/get"), "返回 JSON 应包含 url 字段"
    assert "headers" in data and isinstance(data["headers"], dict), "返回 JSON 应包含 headers 字段"
    assert "origin" in data, "返回 JSON 应包含 origin 字段"

    # 验证实际调用了 MCP Server
    assert "content" in result, "MCP 返回值应包含 'content' 键"

    print("Tested fetch JSON fields successfully.")
