---
name: agent-workflow
description: AI Agent 工作方法论 Skill — 让任何 AI Agent 都能高效、可控、可靠地工作。提供 WBS 任务拆分、P0/P1 分级汇报、安全检查、Context 管理、分层记忆等核心规范。适用于 Claude Code、Cursor、Codex、OpenClaw 等任何 AI agent。
---

# Agent Workflow Skill

**AI Agent 工作方法论 — 让任何 AI Agent 都能高效、可控、可靠地工作**

## 这是什么

一个"工作方法论" Skill，类似于 GTD（Getting Things Done）之于时间管理。

不是又一个 agent 框架，而是告诉任何 AI agent "应该怎么工作"的方法论。

## 核心规范

### P0 规范（所有任务必须遵守）

1. **复杂任务必须拆分** — 文件≥3 / 步骤≥5 / 耗时>15分钟（满足2条）
2. **卡住必须上报** — 失败≥2次 / 等待>30秒
3. **完成必须汇报** — 目标 + 结果 + 产出（3句话）

### P1 规范（复杂任务建议遵守）

4. **批次完成汇报** — 每批次完成后简短汇报
5. **危险操作确认** — git push / 对外发送 / 删除
6. **连续任务插断点** — 连续执行>15分钟插断点

## 任务类型判断

```
收到任务
    ↓
新任务 or 连续任务？
    ↓
简单 or 复杂？（满足2条：文件≥3 / 步骤≥5 / 耗时>15分钟）
    ↓
简单任务 → P0 规范
复杂任务 → P0 + P1 规范
```

## 适用范围

- Claude Code（推荐）
- Cursor
- Codex
- OpenClaw
- 任何支持读取本地文件的 AI agent

## 文档结构

```
agent-workflow/
├── SKILL.md                     # 本文件
├── AGENTS.md                    # 核心规范（必读）
├── IDENTITY.md                  # Agent 身份配置
├── memory/                      # 分层记忆
├── logs/                        # 结构化日志
├── process-standards/           # 完整流程规范
│   ├── core/
│   │   ├── WBS_RULES_v3.0.md
│   │   ├── TASK_REPORTING_v3.0.md
│   │   ├── SECURITY_CHECK.md
│   │   └── CONTEXT_MANAGEMENT_v2.0.md
│   └── templates/
└── scripts/
```

## 快速开始

```bash
# 安装
clawhub install agent-workflow

# 或者 git clone
git clone https://github.com/whhaijun/agent-workflow.git ~/agent-workflow
```

让 Agent 读取 `AGENTS.md` 并遵守所有规范即可开始使用。
