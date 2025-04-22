import requests
from typing import Any, Dict, Tuple
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

def make_mcp_component(name: str, base_url: str):
    """
    Dynamically generate a RagnarokComponent subclass for calling an MCP server.
    """
    info = requests.get(f"{base_url}/info").json()
    # MCP info may list tools under 'tools' key
    tools = info.get("tools") or []
    # Find the tool spec matching the given name
    tool_spec = None
    for tool in tools:
        if tool.get("name") == name:
            tool_spec = tool
            break
    if tool_spec is None:
        raise ValueError(f"Tool '{name}' not found in MCP server at {base_url}")

    # Build input options
    input_opts = []
    for inp in tool_spec.get("inputs", []):
        io_type = ComponentIOType[inp["type"].upper()]
        input_opts.append(
            ComponentInputTypeOption(
                name=inp["name"],
                allowed_types={io_type},
                required=inp.get("required", True),
            )
        )

    # Build output options
    output_opts = []
    for out in tool_spec.get("outputs", []):
        io_type = ComponentIOType[out["type"].upper()]
        output_opts.append(
            ComponentOutputTypeOption(
                name=out["name"],
                type=io_type,
            )
        )

    # Define execute method to invoke the MCP server
    def execute(cls, **kwargs) -> Dict[str, Any]:
        payload = {"tool": name, "args": kwargs}
        resp = requests.post(f"{cls.MCP_BASE_URL}/invoke", json=payload, stream=True)
        try:
            return resp.json()
        except ValueError:
            # Fallback: collect streamed chunks into a text field
            text = "".join(chunk.decode() for chunk in resp.iter_content(1024))
            return {"result": text}

    # Dynamically construct the component class
    attrs = {
        "DESCRIPTION": f"mcp_wrapper_{name}",
        "MCP_BASE_URL": base_url,
        "input_options": classmethod(lambda cls: tuple(input_opts)),
        "output_options": classmethod(lambda cls: tuple(output_opts)),
        "execute": classmethod(execute),
    }
    return type(f"MCPComponent_{name}", (RagnarokComponent,), attrs)
