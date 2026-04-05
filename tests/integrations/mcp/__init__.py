"""
MCP 模块基础测试
"""
import pytest


def test_client_import():
    from integrations.mcp.client import MCPClient
    assert MCPClient is not None


def test_registry_import():
    from integrations.mcp.registry import MCPRegistry
    assert MCPRegistry is not None
