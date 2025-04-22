import asyncio
import logging
from typing import Any, Dict, List, Tuple

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import JSONRPCMessage, Tool  # Tool is defined in mcp.types
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

# NOTE: ClientSession is re‑exported from mcp.client.session after integrating
# the updated implementation provided earlier (with sampling/list_roots/logging
# callbacks, etc.).  If you placed the new class in a different module, adjust
# the import below accordingly.
from mcp.client.session import ClientSession  # type: ignore

# --------------------------------------------------
# Logging setup
# --------------------------------------------------
logger = logging.getLogger("mcp_stdio")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("mcp_stdio.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# --------------------------------------------------
# Cache for generated wrapper classes keyed by (tool, cmd)
# --------------------------------------------------
_stdio_cache: Dict[Tuple[str, Tuple[str, ...]], type] = {}


# --------------------------------------------------
# Helper stream wrappers so we can log full JSON‑RPC traffic
# --------------------------------------------------
class _LoggingWriteStream:
    """Wrap a MemoryObjectSendStream and log every outgoing JSON‑RPC message."""

    def __init__(self, ws):
        self._ws = ws

    async def send(self, msg: JSONRPCMessage):
        try:
            logger.debug("OUT -> %s", msg.model_dump_json(by_alias=True, exclude_none=True))
        except Exception:
            logger.debug("OUT_RAW -> %r", msg)
        return await self._ws.send(msg)

    async def aclose(self):
        return await self._ws.aclose()


class _LoggingReadStream:
    """Wrap a MemoryObjectReceiveStream and log every incoming JSON‑RPC message."""

    def __init__(self, rs):
        self._rs = rs

    async def receive(self):
        msg = await self._rs.receive()
        try:
            logger.debug("IN  <- %s", msg.model_dump_json(by_alias=True, exclude_none=True))
        except Exception:
            logger.debug("IN_RAW <- %r", msg)
        return msg

    async def aclose(self):
        return await self._rs.aclose()


# --------------------------------------------------
# Factory for dynamic MCP‑over‑stdio components
# --------------------------------------------------

def make_stdio_mcp_component(cmd: List[str], tool_name: str) -> type:
    """Create (or fetch from cache) a RagnarokComponent that proxies a tool
    exposed by an MCP server running over stdio.  The server process will be
    launched on first use and kept alive for subsequent calls.
    """
    cache_key: Tuple[str, Tuple[str, ...]] = (tool_name, tuple(cmd))
    if cache_key in _stdio_cache:
        return _stdio_cache[cache_key]

    class _StdioMCPWrapper(RagnarokComponent):
        """Auto‑generated component that forwards calls to an MCP tool."""

        DESCRIPTION = f"mcp_stdio_wrapper_{tool_name}"

        _session: ClientSession | None = None  # shared singleton per tool/cmd
        _tool: Tool | None = None

        # --------------------------------------------
        # Internal helpers
        # --------------------------------------------
        @classmethod
        async def _ensure(cls):
            """Start the MCP server (if needed) and cache the Tool metadata."""
            if cls._session is not None:
                return  # already ready

            # 1. Spawn server process via stdio
            params = StdioServerParameters(command=cmd[0], args=cmd[1:], env=None)
            rs, ws = await stdio_client(params).__aenter__()

            # 2. Wrap streams for logging
            rs = _LoggingReadStream(rs)  # type: ignore
            ws = _LoggingWriteStream(ws)  # type: ignore

            # 3. Establish MCP client session and initialize
            sess = ClientSession(rs, ws)
            await sess.__aenter__()
            await sess.initialize()  # sends initialize + notifications/initialized

            cls._session = sess

            # 4. Discover available tools and locate the requested one
            list_result = await sess.list_tools()
            # new ClientSession returns a ListToolsResult – assume `.tools` list
            tools = getattr(list_result, "tools", list_result)  # fallback for old API
            for t in tools:
                if t.name == tool_name:
                    cls._tool = t
                    break
            if cls._tool is None:
                raise RuntimeError(f"Tool '{tool_name}' not found in server")

        # --------------------------------------------
        # RagnarokComponent API
        # --------------------------------------------
        @classmethod
        async def input_options(cls):
            await cls._ensure()
            assert cls._tool is not None
            return tuple(
                ComponentInputTypeOption(
                    name=i.name,
                    allowed_types={ComponentIOType[i.type.upper()]},
                    required=i.required,
                )
                for i in cls._tool.inputs
            )

        @classmethod
        async def output_options(cls):
            await cls._ensure()
            assert cls._tool is not None
            return tuple(
                ComponentOutputTypeOption(
                    name=o.name,
                    type=ComponentIOType[o.type.upper()],
                )
                for o in cls._tool.outputs
            )

        @classmethod
        async def execute(cls, **kwargs) -> Dict[str, Any]:
            """Invoke the underlying MCP tool with the provided arguments."""
            await cls._ensure()
            assert cls._session is not None
            logger.debug("CALL_TOOL %s args=%s", tool_name, kwargs)
            call_result = await cls._session.call_tool(name=tool_name, arguments=kwargs)

            # The CallToolResult schema typically has a `.results` (list) or is
            # itself indexable; we support both for compatibility.
            output_items = getattr(call_result, "results", call_result)
            if not output_items:
                return {}
            # Serialize the first (or only) output payload to a plain dict
            try:
                return output_items[0].model_dump()
            except AttributeError:
                # already a plain dict or pydantic model
                return output_items[0]  # type: ignore[return‑value]

    # --------------------------------------------------
    # Cache the freshly created wrapper class
    # --------------------------------------------------
    _stdio_cache[cache_key] = _StdioMCPWrapper
    return _StdioMCPWrapper
