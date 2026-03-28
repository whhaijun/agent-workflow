# Smart Agent Skill

**AI Agent 工作方法论 — 让任何 AI Agent 都能高效、可控、可靠地工作**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()

---

## 🎯 这是什么

**Smart Agent 是一个"工作方法论" Skill**，类似于 GTD（Getting Things Done）之于时间管理。

它不是又一个 agent 框架，而是告诉任何 AI agent "应该怎么工作"的方法论。

### 核心能力

| 能力 | 说明 |
|------|------|
| 🧠 自我学习 | 从纠正中学习，持续优化 |
| 📚 分层记忆 | HOT/WARM/COLD 三层，Context 不爆炸 |
| ⚡ 任务拆分 | WBS 规范，防止失控 |
| 📋 任务汇报 | P0/P1 分级，简单任务简单汇报 |
| 🔒 安全检查 | 操作前检查，防止危险操作 |
| 💰 Context 管理 | 实时监控，防止超限 |
| 🎯 流程规范 | 完整的工作流程规范 |

---

## 📦 适用范围

**任何支持读取本地文件的 AI agent：**
- Claude Code（推荐）
- Cursor
- Codex
- Windsurf
- OpenClaw
- 其他 AI coding agent

**核心理念：** 渠道无关，方法论通用

---

## 🚀 快速开始

### 第一步：安装

```bash
# 克隆到本地
git clone https://github.com/yourusername/smart-agent-skill.git ~/.openclaw/workspace/skills/smart-agent

# 或者用于其他 agent
git clone https://github.com/yourusername/smart-agent-skill.git ~/smart-agent
```

### 第二步：配置身份

编辑 `IDENTITY.md`：

```markdown
- **Name**: Ethon
- **Role**: iOS 开发助手
- **Focus**: Swift/OC 开发
```

### 第三步：让 Agent 读取规范

**Claude Code：**
```markdown
# 在 ~/.claude/CLAUDE.md 或项目根目录 CLAUDE.md 中添加：

每次对话开始时：
1. 读取 ~/smart-agent/IDENTITY.md
2. 读取 ~/smart-agent/AGENTS.md
3. 遵守所有规范
```

**Cursor：**
```
Settings → Rules for AI：
读取 ~/smart-agent/AGENTS.md 并遵守所有规范
```

**OpenClaw：**
```
# 已自动加载 workspace/skills/smart-agent
```

---

## 💡 核心规范

### P0 规范（所有任务必须遵守）

**核心 3 条：**
1. **复杂任务必须拆分** — 文件≥3 / 步骤≥5 / 耗时>15分钟（满足2条）
2. **卡住必须上报** — 失败≥2次 / 等待>30秒
3. **完成必须汇报** — 目标 + 结果 + 产出（3句话）

### P1 规范（复杂任务建议遵守）

**额外 3 条：**
4. **批次完成汇报** — 每批次完成后简短汇报
5. **危险操作确认** — git push / 对外发送 / 删除
6. **连续任务插断点** — 连续执行>15分钟插断点

**详细规范：** 见 `process-standards/` 目录

---

## 📚 文档结构

```
smart-agent-skill/
├── README.md                    # 本文件
├── IDENTITY.md                  # Agent 身份配置
├── AGENTS.md                    # 核心规范（必读）
├── memory/                      # 记忆管理
│   ├── hot.md                   # 热记忆（每次加载）
│   ├── projects/                # 项目记忆
│   └── archive/                 # 冷记忆
├── logs/                        # 日志
│   └── YYYY/MM/DD.md
├── process-standards/           # 流程规范
│   ├── README.md                # 规范索引
│   ├── core/                    # 核心规范
│   │   ├── WBS_RULES_v3.0.md
│   │   ├── TASK_REPORTING_v3.0.md
│   │   ├── SECURITY_CHECK.md
│   │   └── CONTEXT_MANAGEMENT_v2.0.md
│   └── templates/               # 模板文件
└── scripts/                     # 工具脚本
    ├── compress_memory.sh
    └── search_memory.sh
```

---

## 🎯 使用示例

### 示例1：简单任务

**任务：** "帮我读一下 README.md"

**Agent 行为：**
1. 判断：新任务 / 简单
2. 使用：P0 规范
3. 执行：直接读取
4. 汇报：目标 + 结果 + 产出

### 示例2：复杂任务

**任务：** "帮我重构支付模块"

**Agent 行为：**
1. 判断：新任务 / 复杂（多文件、多步骤）
2. 使用：P0 + P1 规范
3. 拆分：
   - 批次1：分析现有代码
   - 批次2：设计新架构
   - 批次3：重构代码
4. 每批次完成后汇报
5. 最终汇报

---

## 🔄 和其他 Skill 的关系

**Smart Agent 是"元 Skill"（meta-skill）：**

```
场景：GitHub PR 审查

使用的 skill：
1. smart-agent skill    # 提供工作方法
   - WBS 拆分
   - 任务汇报
   - 记忆管理

2. github skill         # 提供 GitHub 能力
   - gh pr list
   - gh pr view

3. code-review skill    # 提供代码审查规范
   - 安全检查
   - 性能检查

工作流程：
1. smart-agent 指导如何拆分任务
2. github skill 获取 PR 信息
3. code-review skill 执行审查
4. smart-agent 指导如何汇报结果
```

---

## 🌟 核心价值

### 解决的问题

1. **AI agent 容易失控** → WBS 拆分规范
2. **缺少记忆和学习** → 分层记忆 + 自我学习
3. **不同 agent 方法不统一** → 提供统一方法论

### 和其他方案的区别

| 方案 | 定位 | Smart Agent |
|------|------|-------------|
| AutoGPT | Agent 框架 | 工作方法论 |
| LangChain | 工具编排 | 工作方法论 |
| OpenClaw | 运行平台 | 工作方法论 |

**关系：** 互补，不是竞争

---

## 📖 详细文档

- [核心规范](./AGENTS.md) — 必读
- [流程规范索引](./process-standards/README.md) — 完整规范
- [WBS 拆分规范](./process-standards/core/WBS_RULES_v3.0.md)
- [任务汇报规范](./process-standards/core/TASK_REPORTING_v3.0.md)
- [安全检查规范](./process-standards/core/SECURITY_CHECK.md)
- [Context 管理规范](./process-standards/core/CONTEXT_MANAGEMENT_v2.0.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

---

## 📄 License

MIT License

---

## 🙏 致谢

灵感来源：
- GTD（Getting Things Done）
- OpenClaw
- MetaGPT
- 以及所有为 AI agent 生态做出贡献的开发者

---

**让任何 AI agent 都能高效、可控、可靠地工作。**
