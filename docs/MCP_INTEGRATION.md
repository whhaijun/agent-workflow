# MCP 集成完整文档

## 什么是 MCP

**Model Context Protocol**（MCP）是 Anthropic 提出的开放协议，让 AI Agent 能够以标准化方式调用外部工具和资源。每个 MCP Server 暴露一组"工具"（Tool），Agent 通过 JSON-RPC 2.0 协议调用这些工具，获取外部能力（Figma 设计稿、数据库查询、文件操作等）。

架构示意：

```
Agent ──JSON-RPC──► MCP Client ──transport──► MCP Server ──► 外部服务
                         │                         │
                    stdio/HTTP               Figma API
                                             数据库
                                             文件系统
```

---

## stdio vs HTTP/SSE 模式对比

| 维度 | stdio | HTTP/SSE |
|------|-------|----------|
| 适用场景 | 本地 CLI 工具（npx / python 脚本） | 远程部署的 MCP Server |
| 启动方式 | Agent 直接启动子进程 | Server 独立运行，Agent 连接 |
| 通信方式 | stdin / stdout 管道 | HTTP POST + SSE 流 |
| 延迟 | 极低（进程间通信） | 取决于网络 |
| 配置字段 | `command`, `args`, `env` | `url` |
| 典型案例 | Figma MCP、本地工具 | 团队共享 MCP 服务 |

---

## 如何注册新 MCP Server

编辑 `config/mcp_servers.json`，在 `mcp_servers` 数组中追加配置：

### stdio 模式示例

```json
{
  "name": "my-tool",
  "description": "我的自定义工具",
  "transport": "stdio",
  "command": "python3",
  "args": ["/path/to/my_mcp_server.py"],
  "env": {
    "MY_API_KEY": "${MY_API_KEY}"
  },
  "enabled": true
}
```

### HTTP 模式示例

```json
{
  "name": "remote-mcp",
  "description": "远程 MCP 服务",
  "transport": "http",
  "url": "http://localhost:8080/mcp",
  "enabled": true
}
```

### 配置字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | Server 唯一标识符 |
| `description` | 否 | 描述信息 |
| `transport` | 是 | `stdio` 或 `http` |
| `command` | stdio 必填 | 可执行命令 |
| `args` | 否 | 命令行参数列表 |
| `env` | 否 | 环境变量，支持 `${VAR}` 占位符 |
| `url` | http 必填 | MCP Server 地址 |
| `enabled` | 否 | 是否启用，默认 `true` |

---

## 如何在 Agent 中使用

### 基础用法

```python
import asyncio
from integrations.mcp.tool_caller import get_available_tools, call_mcp_tool, shutdown

async def agent_main():
    # 1. 查询可用工具
    tools = await get_available_tools()
    print(f"共 {len(tools)} 个工具可用")

    # 2. 调用工具
    result = await call_mcp_tool(
        tool_name="figma_get_file",
        arguments={"fileKey": "abc123"},
    )
    print("Figma 文件内容:", result)

    # 3. 程序退出前关闭所有连接
    await shutdown()

asyncio.run(agent_main())
```

### 与现有 Agent 集成

在 Agent 的工具列表构建阶段调用 `get_available_tools()`，将返回的 schema 追加到工具定义中：

```python
from integrations.mcp.tool_caller import get_available_tools, call_mcp_tool

class MyAgent:
    async def build_tools(self) -> list[dict]:
        base_tools = [...]          # 内置工具
        mcp_tools = await get_available_tools()
        return base_tools + mcp_tools

    async def dispatch_tool(self, tool_name: str, args: dict):
        # 先尝试 MCP 工具
        mcp_tools = {t["name"] for t in await get_available_tools()}
        if tool_name in mcp_tools:
            return await call_mcp_tool(tool_name, args)
        # 再走内置工具
        return await self._call_builtin(tool_name, args)
```

---

## Figma MCP 接入步骤

### 前置条件

- Node.js >= 18（用于 `npx`）
- Figma Personal Access Token

### 步骤 1：获取 Figma Token

1. 登录 Figma → 头像 → Settings → Personal access tokens
2. 点击 "Generate new token"，复制 token

### 步骤 2：设置环境变量

```bash
# 临时设置（当前终端）
export FIGMA_ACCESS_TOKEN=figd_xxxxxxxxxxxxxxxx

# 永久设置（写入 ~/.zshrc 或 ~/.bashrc）
echo 'export FIGMA_ACCESS_TOKEN=figd_xxxxxxxxxxxxxxxx' >> ~/.zshrc
```

### 步骤 3：启用配置

编辑 `config/mcp_servers.json`，将 figma server 的 `enabled` 改为 `true`：

```json
{
  "name": "figma",
  "enabled": true
}
```

### 步骤 4：验证

```python
import asyncio
from integrations.mcp.tool_caller import get_available_tools

async def test():
    tools = await get_available_tools()
    figma_tools = [t for t in tools if t["_mcp_server"] == "figma"]
    print(f"Figma 工具数: {len(figma_tools)}")
    for t in figma_tools:
        print(f"  - {t['name']}: {t['description']}")

asyncio.run(test())
```

---

## 错误处理

所有 MCP 相关异常均为 `MCPError`：

```python
from integrations.mcp.client import MCPError
from integrations.mcp.tool_caller import call_mcp_tool

try:
    result = await call_mcp_tool("some_tool", {"key": "value"})
except MCPError as e:
    print(f"MCP 错误 [{e.code}]: {e.message}")
    # 常见错误码：
    # -32000  未连接 / 连接失败
    # -32001  请求超时
    # -32002  HTTP 错误
    # -32003  网络连接失败
    # -32601  工具不存在
```

---

## FAQ

**Q: 启动时提示 `npx: command not found`？**

A: 安装 Node.js：`brew install node`（macOS）或前往 https://nodejs.org

**Q: 工具名冲突怎么办？**

A: Registry 会记录警告并保留第一个注册的工具。通过给 server 取不同名称或使用 `{server}_{tool}` 命名约定避免冲突。

**Q: 如何调试 MCP 通信？**

A: 设置日志级别为 DEBUG：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Q: stdio 进程崩溃后会自动重连吗？**

A: 当前版本不支持自动重连。进程崩溃后调用 `shutdown()` 再重新 `initialize()` 即可重连。

**Q: 可以同时连接多个 Figma 账号吗？**

A: 可以，配置两个 server（`name` 不同，`env.FIGMA_ACCESS_TOKEN` 指向不同的环境变量）。
