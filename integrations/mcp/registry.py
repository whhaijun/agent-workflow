"""
MCP Registry — 多 Server 管理与工具路由
从 config/mcp_servers.json 加载配置，聚合所有工具并路由调用
"""

import json
import logging
from pathlib import Path
from typing import Any

from .client import MCPClient, MCPError

logger = logging.getLogger(__name__)

# 配置文件默认路径（相对于项目根目录）
_DEFAULT_CONFIG = Path(__file__).parent.parent.parent / "config" / "mcp_servers.json"


class MCPRegistry:
    """
    MCP Server 注册表。

    职责：
    1. 从 JSON 配置文件加载 server 列表
    2. 按需连接各 server
    3. 聚合工具列表，维护 tool_name → server 的映射
    4. 将工具调用路由到对应 server
    """

    def __init__(self, config_path: str | Path | None = None):
        """
        初始化注册表。

        Args:
            config_path: mcp_servers.json 路径，默认使用项目内 config/mcp_servers.json
        """
        self._config_path = Path(config_path) if config_path else _DEFAULT_CONFIG
        self._clients: dict[str, MCPClient] = {}      # name → MCPClient
        self._tool_index: dict[str, str] = {}          # tool_name → server_name
        self._tool_schemas: list[dict] = []            # 聚合后的工具列表
        self._initialized = False

    # ------------------------------------------------------------------ #
    #  初始化 / 关闭
    # ------------------------------------------------------------------ #

    async def initialize(self) -> None:
        """加载配置并连接所有已启用的 MCP server"""
        if self._initialized:
            return

        configs = self._load_config()
        for cfg in configs:
            if not cfg.get("enabled", True):
                logger.info("[Registry] 跳过已禁用的 server: %s", cfg.get("name"))
                continue
            await self._register_server(cfg)

        self._initialized = True
        logger.info("[Registry] 初始化完成，共加载 %d 个工具", len(self._tool_schemas))

    async def shutdown(self) -> None:
        """断开所有 MCP server 连接"""
        for name, client in self._clients.items():
            try:
                await client.disconnect()
                logger.info("[Registry] 已断开 server: %s", name)
            except Exception as e:
                logger.warning("[Registry] 断开 %s 失败: %s", name, e)
        self._clients.clear()
        self._tool_index.clear()
        self._tool_schemas.clear()
        self._initialized = False

    # ------------------------------------------------------------------ #
    #  Server 注册
    # ------------------------------------------------------------------ #

    async def _register_server(self, cfg: dict) -> None:
        """连接单个 server 并索引其工具"""
        name = cfg.get("name", "unknown")
        try:
            client = MCPClient(cfg)
            await client.connect()
            tools = await client.list_tools()

            for tool in tools:
                tool_name = tool.get("name", "")
                if tool_name in self._tool_index:
                    logger.warning(
                        "[Registry] 工具名冲突: %s 已注册到 %s，跳过 %s",
                        tool_name, self._tool_index[tool_name], name,
                    )
                    continue
                # 在工具描述中附加 server 来源信息
                enriched = {**tool, "_mcp_server": name}
                self._tool_schemas.append(enriched)
                self._tool_index[tool_name] = name

            self._clients[name] = client
            logger.info("[Registry] 已注册 server: %s，工具数: %d", name, len(tools))

        except Exception as e:
            logger.error("[Registry] 注册 server %s 失败: %s", name, e)

    # ------------------------------------------------------------------ #
    #  配置加载
    # ------------------------------------------------------------------ #

    def _load_config(self) -> list[dict]:
        """从 JSON 文件加载 server 配置列表"""
        if not self._config_path.exists():
            logger.warning("[Registry] 配置文件不存在: %s", self._config_path)
            return []

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("mcp_servers", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.error("[Registry] 读取配置文件失败: %s", e)
            return []

    # ------------------------------------------------------------------ #
    #  工具查询与调用
    # ------------------------------------------------------------------ #

    def get_all_tools(self) -> list[dict]:
        """返回所有已注册工具的 schema 列表"""
        return list(self._tool_schemas)

    def get_client_for_tool(self, tool_name: str) -> MCPClient:
        """
        根据工具名查找对应的 MCPClient。

        Raises:
            MCPError: 工具不存在时抛出
        """
        server_name = self._tool_index.get(tool_name)
        if not server_name:
            raise MCPError(-32601, f"工具未注册: {tool_name}")
        client = self._clients.get(server_name)
        if not client:
            raise MCPError(-32000, f"Server 不可用: {server_name}")
        return client

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        路由并调用工具。

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        client = self.get_client_for_tool(tool_name)
        logger.debug("[Registry] 调用工具: %s → server: %s", tool_name, self._tool_index[tool_name])
        return await client.call_tool(tool_name, arguments)

    # ------------------------------------------------------------------ #
    #  异步上下文管理器
    # ------------------------------------------------------------------ #

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, *_):
        await self.shutdown()
