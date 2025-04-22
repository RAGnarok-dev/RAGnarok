import os
import signal
import time
import pytest
import requests

# 根据你的项目结构，修改下面两行的 import 路径
from ragnarok_core.components.official_components.custom_mcp_server_component import CustomMCPServerComponent
from ragnarok_core.components.official_components.mcp_component import make_mcp_component

FETCH_PORT = 3333

@pytest.fixture(scope="module")
def fetch_server():
    # 不再用 .format，直接写固定端口
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

    # 等待 /info 就绪（最多 10s）
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/info", timeout=1)
            if r.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        os.kill(pid, signal.SIGTERM)
        pytest.skip("Fetch MCP Server 未在 10s 内启动")

    yield base_url

    # 测试结束后，优雅终止进程
    os.kill(pid, signal.SIGTERM)

def test_fetch_via_mcp_node(fetch_server):
    """
    将本地启动的 Fetch MCP Server 包装为节点，调用 fetch 工具并断言结果。
    """
    # 生成 Fetch 节点类
    FetchComp = make_mcp_component("fetch", fetch_server)

    # 执行调用
    result = FetchComp.execute(url="https://www.example.com", max_length=500)

    # 断言返回字段和类型
    assert "content" in result, "结果应包含 'content' 字段"
    content = result["content"]
    assert isinstance(content, str), "content 应为字符串"
    assert len(content) > 0, "content 不应为空"

    print("Fetched content length:", len(content))
