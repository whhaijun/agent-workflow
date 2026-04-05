# 更新日志

## v1.4.0 (2026-04-05)

### 新增
- ✅ 原生并行执行能力（环境无关）
  - `integrations/parallel/worker.py` — AgentWorker，独立子进程执行子任务
  - `integrations/parallel/pool.py` — AgentPool，批量并行 + 超时保护 + 错误隔离
  - `integrations/parallel/rpc_server.py` — AgentRPCServer/Client，跨进程工具调用
  - 零外部依赖，全部使用 Python 标准库
  - 兼容无 OpenClaw 环境（Claude Code / Codex / 独立部署）

### 设计原则
- 每批并行上限 max_workers=3（与团队 WBS 规范保持一致）
- 错误隔离：单个 Worker 失败不影响其他 Worker
- 超时保护：每个 Worker 独立超时，不阻塞整体

---

## v1.3.0 (2026-04-05)

### 新增
- MCP（Model Context Protocol）工具调用集成
  - `integrations/mcp/client.py` — MCPClient，支持 stdio 和 HTTP/SSE 双 transport
  - `integrations/mcp/registry.py` — MCPRegistry，多 server 管理与工具路由
  - `integrations/mcp/tool_caller.py` — 统一工具调用接口（get_available_tools / call_mcp_tool）
  - `config/mcp_servers.json` — MCP server 配置文件（含 Figma 示例）
  - `docs/MCP_INTEGRATION.md` — 完整集成文档

### 特性
- JSON-RPC 2.0 协议实现
- 环境变量占位符展开（`${VAR}`）
- 全局 Registry 单例 + 懒初始化
- 工具名冲突检测与告警
- 统一 MCPError 异常体系

---

## v1.2.0 (2026-03-27)

### 新增（P0 完整版）
- ✅ 多 Agent 协作机制
  - `docs/MULTI_AGENT_COLLABORATION.md` — 协作架构、通信协议、冲突避免
  - `scripts/safe_write.sh` — 文件锁机制
- ✅ 性能监控机制
  - `docs/PERFORMANCE_MONITORING.md` — 监控指标、数据分析、可视化
  - `scripts/log_metrics.sh` — 记录性能数据
  - `scripts/generate_report.sh` — 生成周报
  - `reports/` 目录 — 存放性能报告

### 改进
- 更新 README，增加性能监控使用说明
- 完善文件结构说明

---

## v1.1.0 (2026-03-27)

### 新增
- ✅ 自动化脚本
  - `scripts/compress_hot.sh` — 自动压缩 hot.md
  - `scripts/archive_logs.sh` — 自动归档旧日志
  - `scripts/health_check.sh` — 健康检查
- ✅ 记忆压缩规则文档 `docs/MEMORY_COMPRESSION.md`
- ✅ 真实案例 `examples/case-01-ios-dev/`（30天演化过程）
- ✅ 补充缺失目录结构

### 改进
- 更新 README，增加自动化工具使用说明
- 完善文件结构说明

---

## v1.0.0 (2026-03-26)

### 初始版本
- 基础模板结构
- 分层记忆机制
- WBS 任务拆分
- 3高原则 + 第一性原理
