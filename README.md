# AI Agent Template

**自学习 AI Agent 完整模板 — 越用越好用**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 核心特性

- ✅ **自我学习**：从用户纠正中学习，持续优化
- ✅ **分层记忆**：HOT/WARM/COLD 三层，Context 不爆炸
- ✅ **日志可检索**：结构化日志 + 索引，快速查找历史
- ✅ **Token 节省**：智能加载，节省 70% Token
- ✅ **大任务分解**：WBS 自动评估，并行执行
- ✅ **Task Brief**：保持任务上下文，不丢失目标
- ✅ **第一性原理**：从本质出发，找最简解法
- ✅ **安全意识**：红线规则，防止危险操作
- ✅ **错误恢复**：重试 + 降级 + 跳过，不卡住
- ✅ **质量自检**：完成后自动检查，保证质量

## 📦 适用范围

- Claude Code
- Cursor
- Codex
- Windsurf
- 任何支持读取本地文件的 AI coding agent

## 🚀 快速开始

### 1. 克隆模板

```bash
git clone https://gitee.com/[你的用户名]/ai-agent-template.git ~/my-agent
cd ~/my-agent
```

### 2. 配置身份

编辑 `IDENTITY.md`，填写你的 Agent 信息：
- Name: 你的 Agent 名称
- Role: 角色定义
- Focus: 专注领域

### 3. 配置 AI Agent

在 Claude Code / Cursor / Codex 中添加启动指令：

```markdown
每次启动时：
1. 读取 ~/my-agent/IDENTITY.md
2. 读取 ~/my-agent/memory/hot.md
3. 如果项目名匹配，读取 ~/my-agent/memory/projects/[项目名].md
4. 应用所有规则

详细规范见 ~/my-agent/AGENTS.md
```

### 4. 开始使用

Agent 会自动：
- 记录用户纠正到 logs/
- 提炼教训到 memory/hot.md
- 大任务自动拆分
- 完成后质量自检

## 📁 文件结构

```
ai-agent-template/
├── IDENTITY.md          # Agent 身份
├── AGENTS.md            # 工作规范
├── README.md            # 本文件
├── memory/
│   ├── hot.md          # HOT 层（≤100行，每次加载）
│   ├── projects/       # 项目专用知识（按需加载）
│   ├── domains/        # 领域通用知识（按需加载）
│   └── archive/        # 归档（明确查询时加载）
├── logs/
│   ├── index.md        # 日志索引
│   └── 2026/           # 按年月组织
├── tasks/
│   ├── active/         # 进行中的 Task Brief
│   └── archive/        # 已完成的 Task Brief
└── scripts/
    └── search.sh       # 快速搜索脚本
```

## 💡 核心机制

### 分层记忆

| 层级 | 位置 | 大小 | 加载时机 |
|------|------|------|---------|
| HOT | memory/hot.md | ≤100行 | 每次启动 |
| WARM | memory/projects/*.md | ≤200行/文件 | 匹配项目名 |
| COLD | memory/archive/*.md | 无限制 | 明确查询 |

### 自动提升/降级

- 使用 3 次（7天内）→ 提升到 HOT
- 30 天未使用 → 降级到 WARM
- 90 天未使用 → 归档到 COLD

### WBS 任务拆分

满足任意 2 条 → 必须拆分：
- 涉及文件 ≥ 3 个
- 步骤 ≥ 5 步
- 预计耗时 > 10 分钟

## 📊 预期效果

| 时间 | 效果 |
|------|------|
| 第 1 周 | 积累 10-20 条基础规则 |
| 第 1 个月 | 减少 30% 重复纠正 |
| 第 3 个月 | 减少 65% 重复纠正，Token 节省 60% |

## 🔒 安全规则

- 删除文件前必须二次确认
- 不记录密码、API key、token
- 不执行未验证的代码
- 生产环境操作必须明确授权

## 📚 文档

- [完整方案文档](docs/完整方案.md)
- [使用指南](docs/使用指南.md)
- [常见问题](docs/FAQ.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

---

**基于 3 个月实战经验总结**  
**符合 3高原则：高质量 + 高效率 + 高节省**
