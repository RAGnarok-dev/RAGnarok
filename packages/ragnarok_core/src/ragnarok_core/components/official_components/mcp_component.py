import logging
import requests
from typing import Any, Dict, Tuple, List, Optional
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Cache to avoid regenerating identical components
_component_cache: Dict[Tuple[str, str], RagnarokComponent] = {}


def make_mcp_component(
    name: str,
    base_url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 5.0,
    verify_ssl: bool = True
) -> type:
    """
    Factory to dynamically generate a RagnarokComponent subclass for an MCP tool.

    Args:
        name: The MCP tool name to wrap (e.g., 'fetch').
        base_url: The base URL of the MCP server (e.g., 'http://localhost:3333').
        headers: Optional headers to include in all MCP requests.
        timeout: HTTP request timeout in seconds.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        A subclass of RagnarokComponent that implements this MCP tool.

    Raises:
        ValueError: If the named tool is not found in the server's /info response.
        requests.HTTPError: If the /info request returns an HTTP error.
    """
    cache_key = (name, base_url)
    if cache_key in _component_cache:
        return _component_cache[cache_key]

    # Fetch tool metadata
    info_url = f"{base_url.rstrip('/')}/info"
    logger.debug("Requesting MCP /info from %s", info_url)
    resp = requests.get(info_url, headers=headers, timeout=timeout, verify=verify_ssl)
    resp.raise_for_status()
    info = resp.json()

    tools = info.get("tools", [])
    tool_spec = next((t for t in tools if t.get("name") == name), None)
    if not tool_spec:
        raise ValueError(f"Tool '{name}' not found in MCP server at {base_url}")

    # Generate input options
    input_opts = []  # type: List[ComponentInputTypeOption]
    for inp in tool_spec.get("inputs", []):
        io_type = ComponentIOType[inp["type"].upper()]
        input_opts.append(
            ComponentInputTypeOption(
                name=inp.get("name"),
                allowed_types={io_type},
                required=inp.get("required", True),
            )
        )

    # Generate output options
    output_opts = []  # type: List[ComponentOutputTypeOption]
    for out in tool_spec.get("outputs", []):
        io_type = ComponentIOType[out["type"].upper()]
        output_opts.append(
            ComponentOutputTypeOption(
                name=out.get("name"),
                type=io_type,
            )
        )

    # Define the execute method
    def execute(cls, **kwargs) -> Dict[str, Any]:
        payload = {"tool": name, "args": kwargs}
        invoke_url = f"{cls.MCP_BASE_URL.rstrip('/')}/invoke"
        logger.info("Invoking MCP tool '%s' at %s with args %s", name, invoke_url, kwargs)
        try:
            response = requests.post(
                invoke_url,
                headers=cls.MCP_HEADERS,
                json=payload,
                timeout=cls.MCP_TIMEOUT,
                verify=cls.MCP_VERIFY_SSL,
                stream=True
            )
            response.raise_for_status()
            return response.json()
        except requests.JSONDecodeError:
            # Fall back to streaming text
            chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks.append(chunk.decode(errors="ignore"))
            return {"result": ''.join(chunks)}

    # Dynamically build the component class
    attrs = {
        "DESCRIPTION": f"mcp_wrapper_{name}",
        "MCP_BASE_URL": base_url,
        "MCP_HEADERS": headers or {},
        "MCP_TIMEOUT": timeout,
        "MCP_VERIFY_SSL": verify_ssl,
        "input_options": classmethod(lambda cls: tuple(input_opts)),
        "output_options": classmethod(lambda cls: tuple(output_opts)),
        "execute": classmethod(execute),
    }
    component_cls = type(f"MCPComponent_{name}", (RagnarokComponent,), attrs)

    # Cache and return
    _component_cache[cache_key] = component_cls
    return component_cls
