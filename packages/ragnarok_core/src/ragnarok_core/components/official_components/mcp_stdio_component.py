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
_entered_task:  Dict[Tuple[str, ...], asyncio.Task] = {}         # cmd tuple -> task entered
_owns_session_map: Dict[Tuple[str, ...], bool] = {}  # cmd -> True if this task owns it
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
            # todo:这里需要调整
            # ⚠️ 注意：这里只是选取一个 tool 样本来构造 schema，实际执行时仍由 execute 阶段动态决定 tool
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

            async with SessionContextManager(cmd, tool_name) as (sess, tool):
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


class SessionContextManager:
    """
    封装 stdio_client 和 ClientSession 的上下文，确保创建与关闭在同一 Task 中。
    用法：
        async with SessionContextManager(cmd, tool_name) as (sess, tool):
            await sess.call_tool(...)
    """

    def __init__(self, cmd: List[str], tool_name: str):
        self.cmd = tuple(cmd)
        self.tool_name = tool_name
        self.session: ClientSession | None = None
        self.tool: Tool | None = None
        self.cm: AsyncContextManager | None = None
        self.task: asyncio.Task | None = None
        self.key = (self.cmd, self.tool_name)

    async def __aenter__(self) -> Tuple[ClientSession, Tool]:
        if self.key in _session_cache:
            self.session = _session_cache[self.key]
            self.tool = _tool_cache[self.key]
            _owns_session_map[self.key] = False  
            return self.session, self.tool

        self.cm = stdio_client(StdioServerParameters(command=self.cmd[0], args=self.cmd[1:]))
        rs, ws = await self.cm.__aenter__()

        self.session = ClientSession(rs, ws)
        await self.session.__aenter__()
        await self.session.initialize()

        tools = (await self.session.list_tools()).tools
        self.tool = next((t for t in tools if t.name == self.tool_name), None)
        if not self.tool:
            await self.session.__aexit__(None, None, None)
            await self.cm.__aexit__(None, None, None)
            raise RuntimeError(f"Tool '{self.tool_name}' not found in server {self.cmd}")

        _session_cache[self.key] = self.session
        _tool_cache[self.key] = self.tool
        _cm_cache[self.key] = self.cm
        _entered_task[self.key] = asyncio.current_task()
        _owns_session_map[self.key] = True  # ✅ 本次 Task 拥有控制权

        return self.session, self.tool

    async def __aexit__(self, exc_type, exc_val, traceback):
        # ✅ 只有 owner 才能释放
        if not _owns_session_map.get(self.key, False):
            logger.debug("Skip exit for %s: not the session owner", self.key)
            return

        if _entered_task.get(self.key) != asyncio.current_task():
            logger.warning("Skip exit for %s: not in same task", self.key)
            return

        if self.session:
            try:
                await self.session.__aexit__(exc_type, exc_val, traceback)
            except Exception:
                logger.exception("Error closing session %s", self.cmd)

        if self.cm:
            try:
                await self.cm.__aexit__(exc_type, exc_val, traceback)
            except Exception:
                logger.exception("Error closing cm %s", self.key)

        # ✅ 清除所有相关状态
        _session_cache.pop(self.key, None)
        _tool_cache.pop(self.key, None)
        _cm_cache.pop(self.key, None)
        _entered_task.pop(self.key, None)
        _owns_session_map.pop(self.key, None)

    @classmethod
    def get_cached(cls, cmd: List[str], tool_name: str) -> Tuple[ClientSession, Tool] | None:
        key = (tuple(cmd), tool_name)
        # 必须是同一个 Task 创建的 session，才可以复用
        if (
            key in _session_cache
            and key in _tool_cache
            and _entered_task.get(key) == asyncio.current_task()
        ):
            return _session_cache[key], _tool_cache[key]
        return None
