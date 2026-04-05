"""
MCP Tool Caller — 统一工具调用接口
对外暴露两个核心函数：get_available_tools() 和 call_mcp_tool()
"""

import logging
from typing import Any

from .registry import MCPRegistry

logger = logging.getLogger(__name__)

# 全局注册表单例（懒初始化）
_registry: MCPRegistry | None = None


def _get_registry() -> MCPRegistry:
    """获取全局 MCPRegistry 实例（未初始化时自动创建）"""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
    return _registry


async def ensure_initialized() -> MCPRegistry:
    """确保注册表已初始化，返回注册表实例"""
    registry = _get_registry()
    if not registry._initialized:
        await registry.initialize()
    return registry


async def get_available_tools() -> list[dict]:
    """
    返回所有已注册 MCP Server 提供的工具列表。

    每个工具包含：
        - name: 工具名称
        - description: 工具描述
        - inputSchema: JSON Schema 格式的参数定义
        - _mcp_server: 来源 server 名称

    Returns:
        工具 schema 列表，未连接任何 server 时返回空列表

    Example::

        tools = await get_available_tools()
        for tool in tools:
            print(tool["name"], tool["description"])
    """
    registry = await ensure_initialized()
    tools = registry.get_all_tools()
    logger.debug("[ToolCaller] 可用工具数: %d", len(tools))
    return tools


async def call_mcp_tool(tool_name: str, arguments: dict | None = None) -> Any:
    """
    调用指定的 MCP 工具。

    Args:
        tool_name: 工具名称（需与 list_tools 返回的 name 一致）
        arguments: 工具参数字典，默认为空

    Returns:
        工具执行结果（类型由具体工具决定）

    Raises:
        MCPError: 工具不存在、server 不可用或调用失败时抛出

    Example::

        result = await call_mcp_tool(
            "figma_get_file",
            {"fileKey": "abc123"},
        )
        print(result)
    """
    registry = await ensure_initialized()
    arguments = arguments or {}
    logger.info("[ToolCaller] 调用工具: %s，参数: %s", tool_name, arguments)
    result = await registry.call_tool(tool_name, arguments)
    logger.info("[ToolCaller] 工具 %s 调用成功", tool_name)
    return result


async def shutdown() -> None:
    """关闭所有 MCP 连接，释放资源（程序退出时调用）"""
    global _registry
    if _registry is not None:
        await _registry.shutdown()
        _registry = None
        logger.info("[ToolCaller] 所有 MCP 连接已关闭")
