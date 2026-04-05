"""
MCP Client — 支持 stdio 和 HTTP/SSE 两种 transport 模式
遵循 JSON-RPC 2.0 协议
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP 调用异常基类"""
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class MCPClient:
    """
    MCP 客户端，支持 stdio 和 HTTP/SSE 两种 transport。

    stdio 模式：启动本地子进程，通过 stdin/stdout 通信。
    HTTP/SSE 模式：连接远程 MCP Server，通过 HTTP POST 发送请求，SSE 接收流式响应。
    """

    def __init__(self, config: dict):
        """
        初始化 MCPClient。

        Args:
            config: server 配置字典，包含 transport / command / url 等字段
        """
        self.config = config
        self.name = config.get("name", "unknown")
        self.transport = config.get("transport", "stdio")  # stdio | http

        # stdio 模式状态
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._pending: dict[str, asyncio.Future] = {}

        # HTTP 模式状态
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url: str = config.get("url", "")

        self._connected = False

    # ------------------------------------------------------------------ #
    #  连接 / 断开
    # ------------------------------------------------------------------ #

    async def connect(self) -> None:
        """建立与 MCP Server 的连接"""
        if self._connected:
            return

        if self.transport == "stdio":
            await self._connect_stdio()
        elif self.transport in ("http", "sse"):
            await self._connect_http()
        else:
            raise MCPError(-32000, f"不支持的 transport 类型: {self.transport}")

        self._connected = True
        logger.info("[MCP:%s] 已连接 (%s)", self.name, self.transport)

    async def disconnect(self) -> None:
        """断开连接并释放资源"""
        if not self._connected:
            return

        if self.transport == "stdio":
            await self._disconnect_stdio()
        elif self.transport in ("http", "sse"):
            await self._disconnect_http()

        self._connected = False
        logger.info("[MCP:%s] 已断开", self.name)

    # ------------------------------------------------------------------ #
    #  stdio transport
    # ------------------------------------------------------------------ #

    async def _connect_stdio(self) -> None:
        """启动本地子进程"""
        command = self.config.get("command", "")
        args = self.config.get("args", [])
        env_overrides = self.config.get("env", {})

        # 展开环境变量占位符（${VAR}）
        env = os.environ.copy()
        for key, val in env_overrides.items():
            if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
                env_key = val[2:-1]
                env[key] = os.environ.get(env_key, "")
            else:
                env[key] = val

        self._process = await asyncio.create_subprocess_exec(
            command, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # 后台循环读取 stdout
        self._reader_task = asyncio.create_task(self._stdio_reader_loop())

    async def _disconnect_stdio(self) -> None:
        """终止子进程"""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except Exception:
                self._process.kill()

    async def _stdio_reader_loop(self) -> None:
        """持续读取子进程 stdout，解析 JSON-RPC 响应并派发到对应 Future"""
        assert self._process and self._process.stdout
        while True:
            try:
                line = await self._process.stdout.readline()
                if not line:
                    break
                data = json.loads(line.decode())
                req_id = str(data.get("id", ""))
                if req_id in self._pending:
                    fut = self._pending.pop(req_id)
                    if "error" in data:
                        err = data["error"]
                        fut.set_exception(MCPError(err.get("code", -1), err.get("message", ""), err.get("data")))
                    else:
                        fut.set_result(data.get("result"))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("[MCP:%s] stdio 读取异常: %s", self.name, e)

    async def _stdio_request(self, method: str, params: dict, timeout: float = 30) -> Any:
        """通过 stdin 发送 JSON-RPC 请求并等待响应"""
        assert self._process and self._process.stdin

        req_id = str(uuid.uuid4())
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }) + "\n"

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut

        self._process.stdin.write(payload.encode())
        await self._process.stdin.drain()

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise MCPError(-32001, f"请求超时 (method={method})")

    # ------------------------------------------------------------------ #
    #  HTTP/SSE transport
    # ------------------------------------------------------------------ #

    async def _connect_http(self) -> None:
        """创建 aiohttp Session"""
        self._session = aiohttp.ClientSession()

    async def _disconnect_http(self) -> None:
        """关闭 aiohttp Session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def _http_request(self, method: str, params: dict, timeout: float = 30) -> Any:
        """发送 HTTP POST JSON-RPC 请求"""
        assert self._session

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }

        try:
            async with self._session.post(
                self._base_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    raise MCPError(-32002, f"HTTP 错误 {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as e:
            raise MCPError(-32003, f"HTTP 连接失败: {e}")

        if "error" in data:
            err = data["error"]
            raise MCPError(err.get("code", -1), err.get("message", ""), err.get("data"))

        return data.get("result")

    # ------------------------------------------------------------------ #
    #  统一请求入口
    # ------------------------------------------------------------------ #

    async def _request(self, method: str, params: dict | None = None, timeout: float = 30) -> Any:
        """根据 transport 类型路由请求"""
        if not self._connected:
            raise MCPError(-32000, f"[MCP:{self.name}] 未连接，请先调用 connect()")

        params = params or {}
        if self.transport == "stdio":
            return await self._stdio_request(method, params, timeout)
        else:
            return await self._http_request(method, params, timeout)

    # ------------------------------------------------------------------ #
    #  MCP 核心方法
    # ------------------------------------------------------------------ #

    async def list_tools(self) -> list[dict]:
        """
        获取 MCP Server 支持的工具列表。

        Returns:
            list of tool descriptors，每个元素包含 name / description / inputSchema
        """
        result = await self._request("tools/list")
        return result.get("tools", []) if isinstance(result, dict) else []

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        调用指定工具。

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具返回的内容
        """
        result = await self._request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return result

    async def list_resources(self) -> list[dict]:
        """
        获取 MCP Server 提供的资源列表。

        Returns:
            list of resource descriptors，每个元素包含 uri / name / mimeType
        """
        result = await self._request("resources/list")
        return result.get("resources", []) if isinstance(result, dict) else []

    async def read_resource(self, uri: str) -> Any:
        """
        读取指定资源内容。

        Args:
            uri: 资源 URI

        Returns:
            资源内容
        """
        result = await self._request("resources/read", {"uri": uri})
        return result

    # ------------------------------------------------------------------ #
    #  异步上下文管理器
    # ------------------------------------------------------------------ #

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_):
        await self.disconnect()
