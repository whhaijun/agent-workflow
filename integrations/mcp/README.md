# MCP 集成模块

支持通过 **Model Context Protocol** 调用外部工具（Figma、TAPD、数据库等）。

## 文件结构

```
integrations/mcp/
├── __init__.py       # 模块入口
├── client.py         # MCPClient（stdio / HTTP/SSE）
├── registry.py       # MCPRegistry（多 server 管理）
├── tool_caller.py    # 统一调用接口（对外使用这个）
└── README.md         # 本文件
```

## 快速开始

### 1. 编辑配置

`config/mcp_servers.json` 中添加 server，将 `enabled` 设为 `true`：

```json
{
  "mcp_servers": [
    {
      "name": "figma",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@southleft/figma-console-mcp"],
      "env": { "FIGMA_ACCESS_TOKEN": "${FIGMA_ACCESS_TOKEN}" },
      "enabled": true
    }
  ]
}
```

### 2. 设置环境变量

```bash
export FIGMA_ACCESS_TOKEN=your_token_here
```

### 3. 代码调用

```python
from integrations.mcp.tool_caller import get_available_tools, call_mcp_tool, shutdown

async def main():
    # 列出所有工具
    tools = await get_available_tools()
    for t in tools:
        print(t["name"], "-", t["description"])

    # 调用工具
    result = await call_mcp_tool("figma_get_file", {"fileKey": "abc123"})
    print(result)

    # 程序退出前关闭连接
    await shutdown()
```

## Transport 模式

| 模式 | 适用场景 | 配置字段 |
|------|----------|----------|
| `stdio` | 本地 CLI 工具（npx / python） | `command`, `args`, `env` |
| `http` | 远程 MCP Server | `url` |

## 错误处理

所有异常统一为 `MCPError`，包含 `code` / `message` / `data` 字段。

详细文档见 `docs/MCP_INTEGRATION.md`。
