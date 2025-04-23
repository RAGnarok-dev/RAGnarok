# ragnarok_core/components/official_components/mcp_stdio_component.py
import asyncio
import logging
import atexit, anyio
from typing import Any, Dict, List, Tuple
from typing import AsyncContextManager

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import JSONRPCMessage, Tool
from mcp.client.session import ClientSession  # type: ignore
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

# -------------------------------------------------- logging --------------------------------------------------
logger = logging.getLogger("mcp_stdio")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("mcp_stdio.log")
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(fh)

# -------------------------------------------------- caches ---------------------------------------------------
_wrapper_cache: Dict[str, type] = {}                        # tool_name -> wrapper class
_session_cache: Dict[Tuple[str, ...], ClientSession] = {}   # cmd tuple -> ClientSession
_tool_cache:    Dict[Tuple[str, ...], Tool] = {}            # cmd tuple -> Tool
_cm_cache:      Dict[Tuple[str, ...], AsyncContextManager] = {}  # cmd tuple -> stdio cm

# -------------------------------------------------- stream wrappers -----------------------------------------
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

# -------------------------------------------------- factory --------------------------------------------------
def make_stdio_mcp_component(tool_name: str) -> type:
    """
    生成一个组件：运行时接收 `cmd: List[str]`，用 stdio 启动 / 复用 MCP 服务器并调用指定 tool。
    """
    if tool_name in _wrapper_cache:
        return _wrapper_cache[tool_name]

    class _StdioMCPWrapper(RagnarokComponent):
        DESCRIPTION = f"mcp_stdio_dyn_{tool_name}"
        ENABLE_HINT_CHECK = False
        _lock: asyncio.Lock = asyncio.Lock()                 # 保护初始化

        # -------- helpers --------
        @classmethod
        async def _get_session_tool(cls, cmd: List[str]) -> Tuple[ClientSession, Tool]:
            key = tuple(cmd)
            if key in _session_cache:
                return _session_cache[key], _tool_cache[key]

            async with cls._lock:
                if key in _session_cache:
                    return _session_cache[key], _tool_cache[key]

                # ① 进入 stdio_client ctx，但不退出
                cm = stdio_client(StdioServerParameters(command=cmd[0], args=cmd[1:]))
                rs, ws = await cm.__aenter__()

                # ② 建立会话并初始化
                sess = ClientSession(rs, ws)
                await sess.__aenter__(); await sess.initialize()

                # ③ 查找 tool
                tools = (await sess.list_tools()).tools
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool is None:
                    await cm.__aexit__(None, None, None)
                    raise RuntimeError(f"Tool '{tool_name}' not found in server {cmd}")

                # ④ 缓存
                _session_cache[key] = sess
                _tool_cache[key]    = tool
                _cm_cache[key]      = cm
                return sess, tool

        # -------- component I/O schema --------
        @classmethod
        def input_options(cls):
            base = [
                ComponentInputTypeOption(
                    name="cmd",
                    allowed_types={ComponentIOType.LIST_STRING},
                    required=True,
                )
            ]
            if _tool_cache:
                any_tool = next(iter(_tool_cache.values()))
                base.extend(
                    ComponentInputTypeOption(i.name, {ComponentIOType[i.type.upper()]}, i.required)
                    for i in any_tool.inputs
                )
            return tuple(base)

        @classmethod
        def output_options(cls):
            if _tool_cache:
                any_tool = next(iter(_tool_cache.values()))
                return tuple(
                    ComponentOutputTypeOption(o.name, ComponentIOType[o.type.upper()])
                    for o in any_tool.outputs
                )
            return (ComponentOutputTypeOption("result", ComponentIOType.JSON),)

        # -------- execute --------
        @classmethod
        async def execute(cls, **kwargs) -> Dict[str, Any]:
            if "cmd" not in kwargs:
                raise ValueError("missing required input 'cmd'")
            cmd: List[str] = kwargs.pop("cmd")

            sess, _ = await cls._get_session_tool(cmd)
            logger.debug("CALL_TOOL %s via %s args=%s", tool_name, cmd, kwargs)
            res = await sess.call_tool(name=tool_name, arguments=kwargs)

            items = getattr(res, "content", res)
            if not items:
                return {}
            first = items[0]

            if hasattr(first, "model_dump"):
                return first.model_dump()
            if hasattr(first, "dict"):
                return first.dict()
            if isinstance(first, str):
                return {"text": first}
            return {"raw": first}

    _wrapper_cache[tool_name] = _StdioMCPWrapper
    return _StdioMCPWrapper

# -------------------------------------------------- graceful shutdown ----------------------------------------
async def _shutdown_all_stdio_sessions() -> None:
    # 1. 关闭 ClientSession
    for key, sess in list(_session_cache.items()):
        try:
            if hasattr(sess, "aclose"):                       # 新版接口
                await sess.aclose()
            else:                                             # 老版 fallback
                await sess.__aexit__(None, None, None)
        except Exception:
            logger.exception("Error closing session %s", key)

    # 2. 退出 stdio_client 的 async-context-manager
    for key, cm in list(_cm_cache.items()):
        try:
            await cm.__aexit__(None, None, None)
        except Exception:
            logger.exception("Error closing cm %s", key)

    # 3. 清空缓存，防止再次回收时重复关闭
    _session_cache.clear()
    _tool_cache.clear()
    _cm_cache.clear()

# atexit.register(lambda: anyio.run(_shutdown_all_stdio_sessions))
