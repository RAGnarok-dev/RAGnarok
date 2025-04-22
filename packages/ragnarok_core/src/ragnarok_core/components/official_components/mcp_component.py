import requests
from typing import Any, Dict, Tuple
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

def make_mcp_component(name: str, base_url: str):
    # 1. 拉取 /info，动态生成输入输出声明
    info = requests.get(f"{base_url}/info").json()
    input_opts = [
        ComponentInputTypeOption(
            name=inp["name"],
            allowed_types={ComponentIOType[inp["type"].upper()]},
            required=inp.get("required", True),
        )
        for inp in info["inputs"]
    ]
    output_opts = [
        ComponentOutputTypeOption(
            name=out["name"],
            type=ComponentIOType[out["type"].upper()]
        )
        for out in info["outputs"]
    ]

    # 2. 构建 execute 调用 /invoke
    def execute(cls, **kwargs):
        payload = {"tool": name, "args": kwargs}
        resp = requests.post(f"{cls.MCP_BASE_URL}/invoke", json=payload, stream=True)
        # 如果是纯JSON返回：
        try:
            return resp.json()
        except ValueError:
            # SSE 流式解析（示例简化，仅收集 chunk）
            text = "".join(chunk.decode() for chunk in resp.iter_content(1024))
            return {"result": text}

    # 3. 动态创建组件类
    attrs = {
        "DESCRIPTION": f"mcp_wrapper_{name}",
        "MCP_BASE_URL": base_url,
        "input_options": classmethod(lambda cls: tuple(input_opts)),
        "output_options": classmethod(lambda cls: tuple(output_opts)),
        "execute": classmethod(execute),
    }
    return type(f"MCPComponent_{name}", (RagnarokComponent,), attrs)
