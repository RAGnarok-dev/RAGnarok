import asyncio
import logging
from typing import Any, Dict, List, Tuple

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import JSONRPCMessage, Tool
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)
from mcp.client.session import ClientSession  # type: ignore

# --------------------------------------------------
# logging
# --------------------------------------------------
logger = logging.getLogger("mcp_stdio")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("mcp_stdio.log")
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(fh)

# --------------------------------------------------
# caches
# --------------------------------------------------
_wrapper_cache: Dict[str, type] = {}          # key = tool_name
_session_cache: Dict[Tuple[str, ...], Tuple[ClientSession, Tool]] = {}
_tool_meta_cache: Dict[Tuple[str, ...], Tool] = {}  # 方便 input/output_options 查询

# --------------------------------------------------
# stream wrappers
# --------------------------------------------------
class _LoggingWriteStream:
    def __init__(self, ws): self._ws = ws
    async def send(self, msg: JSONRPCMessage):
        try:
            logger.debug("OUT -> %s", msg.model_dump_json(by_alias=True, exclude_none=True))
        except Exception:
            logger.debug("OUT_RAW -> %r", msg)
        return await self._ws.send(msg)
    async def aclose(self): return await self._ws.aclose()

class _LoggingReadStream:
    def __init__(self, rs): self._rs = rs
    async def receive(self):
        msg = await self._rs.receive()
        try:
            logger.debug("IN  <- %s", msg.model_dump_json(by_alias=True, exclude_none=True))
        except Exception:
            logger.debug("IN_RAW <- %r", msg)
        return msg
    async def aclose(self): return await self._rs.aclose()

# --------------------------------------------------
# factory
# --------------------------------------------------
def make_stdio_mcp_component(tool_name: str) -> type:
    """
    返回一个 RagnarokComponent；其输入里必须包含 `cmd: List[str]`，
    运行时会启动/复用该 cmd 所在的 MCP server，并调用给定 tool。
    """
    if tool_name in _wrapper_cache:
        return _wrapper_cache[tool_name]

    class _StdioMCPWrapper(RagnarokComponent):
        DESCRIPTION = f"mcp_stdio_dyn_{tool_name}"
        ENABLE_HINT_CHECK = False

        _lock: asyncio.Lock = asyncio.Lock()   # 保护 _session_cache 初始化

        # ---------- helpers ----------
        @classmethod
        async def _get_session_tool(cls, cmd: List[str]) -> Tuple[ClientSession, Tool]:
            key = tuple(cmd)
            if key in _session_cache:
                return _session_cache[key]

            async with cls._lock:
                if key in _session_cache:      # 双重检查
                    return _session_cache[key]

                # 1) spawn server
                params = StdioServerParameters(command=cmd[0], args=cmd[1:])
                rs, ws = await stdio_client(params).__aenter__()
                rs, ws = _LoggingReadStream(rs), _LoggingWriteStream(ws)

                sess = ClientSession(rs, ws)
                await sess.__aenter__(); await sess.initialize()

                # 2) locate tool
                tools = getattr(await sess.list_tools(), "tools", None) or []
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool is None:
                    raise RuntimeError(f"Tool '{tool_name}' not found in server launched by {cmd}")

                # 3) cache
                _session_cache[key] = (sess, tool)
                _tool_meta_cache[key] = tool
                return sess, tool

        # ---------- component API ----------
        @classmethod
        def input_options(cls):
            # cmd 一定要
            base: List[ComponentInputTypeOption] = [
                ComponentInputTypeOption(
                    name="cmd",
                    allowed_types={ComponentIOType.LIST_STRING},
                    required=True,
                )
            ]
            # 若已有任意 cmd 的 tool 元数据，补充真实输入字段 (取首个即可)
            if _tool_meta_cache:
                any_tool = next(iter(_tool_meta_cache.values()))
                base.extend(
                    ComponentInputTypeOption(
                        i.name, {ComponentIOType[i.type.upper()]}, i.required
                    )
                    for i in any_tool.inputs
                )
            return tuple(base)

        @classmethod
        def output_options(cls):
            std = [ComponentOutputTypeOption("result", ComponentIOType.JSON)]
            if _tool_meta_cache:
                any_tool = next(iter(_tool_meta_cache.values()))
                std = [
                    ComponentOutputTypeOption(o.name, ComponentIOType[o.type.upper()])
                    for o in any_tool.outputs
                ]
            return tuple(std)

        @classmethod
        async def execute(cls, **kwargs) -> Dict[str, Any]:
            if "cmd" not in kwargs:
                raise ValueError("missing required input 'cmd'")
            cmd: List[str] = kwargs.pop("cmd")
            sess, tool = await cls._get_session_tool(cmd)

            logger.debug("CALL_TOOL %s via %s args=%s", tool_name, cmd, kwargs)
            res = await sess.call_tool(name=tool_name, arguments=kwargs)

            items = getattr(res, "results", res)
            if not items:
                return {}
            first = items[0]
            try:
                return first.model_dump()
            except AttributeError:
                return first  # plain dict / primitive

    _wrapper_cache[tool_name] = _StdioMCPWrapper
    return _StdioMCPWrapper
