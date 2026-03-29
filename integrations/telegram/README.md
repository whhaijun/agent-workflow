# Telegram Bot Integration

## 快速开始

### 1. 安装依赖

```bash
pip install python-telegram-bot
# 根据选择的 AI 引擎安装对应的库
pip install openai      # OpenAI
pip install anthropic   # Claude
# DeepSeek 使用 openai 库
# Ollama 使用 openai 库
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写配置
```

### 3. 启动 Bot

```bash
cd integrations/telegram
python bot.py
```

## 支持的 AI 引擎

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Claude**: Claude Sonnet 4, Claude Opus
- **DeepSeek**: DeepSeek Chat（国内可用）
- **Ollama**: 本地模型（免费）

## 文档

详细文档请查看：`docs/TELEGRAM_INTEGRATION.md`

## 示例

```python
# 使用 OpenAI
AI_ENGINE=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# 使用 Claude
AI_ENGINE=claude
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4

# 使用 DeepSeek
AI_ENGINE=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# 使用 Ollama（本地）
AI_ENGINE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## 特性

- ✅ 多 AI 引擎支持
- ✅ 统一接口设计
- ✅ 类型安全
- ✅ 错误处理
- ✅ 日志记录
- ✅ 可扩展架构

---

**版本**: v1.0.0  
**更新日期**: 2026-03-28
