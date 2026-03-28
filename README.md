# Smart Agent Template

**自学习 AI Agent 完整模板 — 越用越好用**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()

---

## 🎯 核心特性

| 能力 | 说明 |
|------|------|
| 🧠 自我学习 | 从用户纠正中学习，持续优化 |
| 📚 分层记忆 | HOT/WARM/COLD 三层，Context 不爆炸 |
| 🔍 日志可检索 | 结构化日志 + 索引，快速查找历史 |
| 💰 Token 节省 | 智能加载，节省 70% Token |
| ⚡ 大任务分解 | WBS 自动评估，并行执行 |
| 📋 Task Brief | 保持任务上下文，不丢失目标 |
| 🧩 第一性原理 | 从本质出发，找最简解法 |
| 🎯 3高原则 | 高质量 + 高效率 + 高节省 |
| 🔒 安全意识 | 红线规则，防止危险操作 |
| ✅ 质量自检 | 完成后自动检查，保证质量 |
| 🆕 **流程规范** | **完整的 WBS/汇报/安全/Context 管理规范** |

---

## 📦 适用范围

- **Claude Code**（推荐）
- Cursor
- Codex
- Windsurf
- 任何支持读取本地文件的 AI coding agent

---

## 🚀 快速开始

### 第一步：克隆模板

```bash
git clone https://gitee.com/sihj/smart-agent-template.git ~/my-agent
cd ~/my-agent
```

### 第二步：配置身份

编辑 `IDENTITY.md`，填写你的 Agent 信息：

```markdown
- **Name**: Ethon          # 你的 Agent 名称
- **Role**: iOS 开发助手   # 角色定义
- **Focus**: Swift/OC 开发 # 专注领域
```

### 第三步：配置 AI Agent 启动指令

在 Claude Code / Cursor / Codex 中添加以下启动指令：

**Claude Code（`~/.claude/CLAUDE.md` 或项目根目录 `CLAUDE.md`）：**

```markdown
# Agent Startup

每次对话开始时，自动执行：
1. 读取 ~/my-agent/IDENTITY.md
2. 读取 ~/my-agent/memory/hot.md
3. 如果当前项目名匹配，读取 ~/my-agent/memory/projects/[项目名].md
4. 应用 ~/my-agent/AGENTS.md 中的所有规则
```

**Cursor（Settings → Rules for AI）：**

```
每次启动读取：~/my-agent/IDENTITY.md 和 ~/my-agent/memory/hot.md
遵守 ~/my-agent/AGENTS.md 中的所有规则
```

### 第四步：开始使用

直接和 Agent 对话，它会自动学习和优化。

---

## 💡 使用示例

### 示例 1：Agent 自动学习

```
你：这个函数命名不对，应该用驼峰命名

Agent：
1. 立即记录到 ~/my-agent/logs/2026/03/26.md：
   ## 14:30 - 函数命名规范
   - 纠正：应该用驼峰命名
   - 教训：函数名必须用 camelCase
   - 下次：自动检查所有函数命名

2. 更新 ~/my-agent/memory/hot.md：
   ## 代码规范
   - 函数命名：必须用驼峰（camelCase）

3. 下次对话自动应用此规则 ✅
```

---

### 示例 2：大任务自动拆分

```
你：帮我分析项目里所有的 ViewController，找出不符合规范的

Agent（WBS 评估）：
- 涉及文件 ≥ 3 个 ✅
- 步骤 ≥ 5 步 ✅
→ 满足 2 条，必须拆分

拆分方案：
1. 子任务 1：扫描所有 ViewController 文件列表（1分钟）
2. 子任务 2：检查命名规范（1分钟）
3. 子任务 3：检查 weakSelf 使用（1分钟）
4. 子任务 4：检查注释规范（1分钟）

并行执行 1-4，完成后统一汇报 ✅
```

---

### 示例 3：Task Brief 保持上下文

```
你：帮我实现批量发工资功能

Agent 自动创建 Task Brief：
## 任务 ID: TB-2026-03-26-001
## 目标: 实现批量发工资功能
## 标准:
  - [ ] 支持多选员工
  - [ ] 批量输入金额
  - [ ] 确认后批量发送
  - [ ] 显示发送结果
## 交付物: PaymentBatchViewController.m

→ 整个开发过程中，Agent 始终知道目标是什么 ✅
```

---

### 示例 4：3高原则评估工具

```
你：我们要选一个 UI 测试框架，XCUITest 还是 Maestro？

Agent（3高原则评估）：

| 维度 | XCUITest | Maestro |
|------|---------|---------|
| 高质量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 高效率 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 高节省 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

结论：Maestro 更符合 3高原则，推荐使用 ✅
```

---

### 示例 5：搜索历史日志

```bash
# 搜索所有关于 weakSelf 的历史记录
cd ~/my-agent && ./scripts/search.sh "weakSelf"

# 输出：
# logs/2026/03/20.md: - 纠正：忘记加 weakSelf
# logs/2026/03/26.md: - 教训：block 里必须用 weakSelf
```

---

## 📁 文件结构

```
my-agent/
├── IDENTITY.md              # Agent 身份（修改这里）
├── AGENTS.md                # 工作规范（核心规则）
├── README.md                # 本文件
├── memory/
│   ├── hot.md              # HOT 层（≤100行，每次加载）
│   ├── projects/
│   │   └── PROJECT_TEMPLATE.md  # 项目模板（复制并重命名）
│   ├── domains/            # 领域知识（如 ios.md, testing.md）
│   └── archive/            # 归档（90天未用自动降级）
├── logs/
│   ├── index.md            # 日志索引（关键词 → 日期）
│   └── 2026/03/            # 按年月组织
├── tasks/
│   ├── TEMPLATE.md         # Task Brief 模板
│   ├── active/             # 进行中的任务
│   └── archive/            # 已完成的任务
└── scripts/
    ├── search.sh           # 快速搜索脚本
    ├── compress_hot.sh     # 自动压缩 hot.md
    ├── archive_logs.sh     # 自动归档旧日志
    ├── health_check.sh     # 健康检查
    ├── safe_write.sh       # 安全写入（文件锁）
    ├── log_metrics.sh      # 记录性能指标
    └── generate_report.sh  # 生成性能周报
├── docs/
│   ├── MEMORY_COMPRESSION.md  # 记忆压缩规则
│   ├── MULTI_AGENT_COLLABORATION.md  # 多 Agent 协作
│   └── PERFORMANCE_MONITORING.md  # 性能监控
├── examples/
│   └── case-01-ios-dev/    # 真实案例（30天演化）
└── reports/                # 性能报告
```

---

## 🔄 记忆分层机制

| 层级 | 文件 | 大小限制 | 加载时机 | 降级规则 |
|------|------|---------|---------|---------|
| HOT | memory/hot.md | ≤100行 | 每次启动 | 30天未用 → WARM |
| WARM | memory/projects/*.md | ≤200行/文件 | 匹配项目名 | 90天未用 → COLD |
| COLD | memory/archive/*.md | 无限制 | 明确查询 | 永久保留 |

---

## 📊 预期效果

| 时间 | 效果 |
|------|------|
| 第 1 周 | 积累 10-20 条基础规则，减少重复纠正 |
| 第 1 个月 | HOT memory 稳定，减少 30% 重复纠正 |
| 第 3 个月 | 减少 65% 重复纠正，Token 节省 60% |

---

## 📋 流程规范（v2.0 新增）

完整的团队协作流程规范，包含 WBS 拆分、任务汇报、安全检查、Context 管理。

### 核心规范文档

所有规范文档位于 `process-standards/` 目录：

| 文档 | 说明 |
|------|------|
| `README.md` | 规范索引，新成员必读 |
| `core/WBS_RULES_v2.0.md` | WBS 拆分规范（含连续任务触发条件、强制断点） |
| `core/TASK_REPORTING_v2.0.md` | 任务汇报规范（5个强制检查点、标准格式） |
| `core/SECURITY_CHECK.md` | 安全检查规范（操作前检查清单、敏感数据识别） |
| `core/CONTEXT_MANAGEMENT_v2.0.md` | Context 管理规范（实时监控、预警机制） |
| `core/TEAM_PROTOCOL.md` | 团队协作协议（通信协议、Task Brief 格式） |

### 模板文件

直接复制使用的模板：

- `templates/task_brief_template.md` — 跨 agent 传递任务
- `templates/wbs_template.md` — 任务拆分方案
- `templates/report_template.md` — 任务汇报
- `templates/security_check_template.md` — 安全检查

### 快速开始

1. **新成员必读**（按顺序）：
   - `process-standards/README.md` — 规范索引（5分钟）
   - `core/WBS_RULES_v2.0.md` — WBS 拆分规范（5分钟）
   - `core/TASK_REPORTING_v2.0.md` — 任务汇报规范（5分钟）

2. **执行任务时**：
   - 收到任务 → 先评估是否需要拆分（WBS_RULES）
   - 每个批次完成 → 输出阶段汇报（TASK_REPORTING）
   - 危险操作前 → 执行安全检查（SECURITY_CHECK）
   - Context > 70% → 采取优化措施（CONTEXT_MANAGEMENT）

3. **实施计划**：
   - 详见 `process-standards/IMPLEMENTATION_PLAN_v2.0.md`
   - 预计 1 周完成 P0（文档整理、规则学习、试运行）
   - 预计 2 周完成 P1（安全诊断、Context 管理）

### 预期效果

| 指标 | 改善率 |
|------|--------|
| 任务超时率 | -40% |
| Context 超限率 | -60% |
| 汇报格式规范率 | +50% |
| 安全事故次数 | -80% |
| 文档查找时间 | -70% |

---

## 🔒 安全规则

- 删除文件前必须二次确认
- 不记录密码、API key、token（自动脱敏）
- 不执行未验证的代码
- 生产环境操作必须明确授权

---

## 📄 License

MIT License — 自由使用，无需署名

---

## 🛠️ 自动化工具

### 健康检查
```bash
cd ~/my-agent
./scripts/health_check.sh
```

### 压缩 hot.md
```bash
# 当 hot.md 超过 100 行时运行
./scripts/compress_hot.sh
```

### 归档旧日志
```bash
# 归档 90 天前的日志
./scripts/archive_logs.sh
```

### 性能监控
```bash
# 记录性能数据（Agent 自动调用）
./scripts/log_metrics.sh 1200 800 "代码开发" "是" 0 5

# 生成周报
./scripts/generate_report.sh
```

详细说明：
- 记忆压缩：`docs/MEMORY_COMPRESSION.md`
- 多 Agent 协作：`docs/MULTI_AGENT_COLLABORATION.md`
- 性能监控：`docs/PERFORMANCE_MONITORING.md`

---

## 📚 真实案例

查看 `examples/case-01-ios-dev/` 了解：
- 第 1 天到第 30 天的演化过程
- hot.md 如何从空白到 85 行
- Token 消耗如何减少 60%

---

**基于 3 个月实战经验总结 | 符合 3高原则：高质量 + 高效率 + 高节省**
