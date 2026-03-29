# Telegram Bot 集成指南

## 📋 概述

本指南介绍如何将 Telegram Bot 集成到 smart-agent-template，实现多渠道 Agent 通信。

## 🎯 核心特性

- ✅ 统一消息格式
- ✅ 多 Agent 通信支持
- ✅ 可插拔 AI 引擎
- ✅ 类型安全
- ✅ 错误处理

## 📁 文件结构

```
smart-agent-template/
├── integrations/
│   └── telegram/
│       ├── bot.py              # Bot 主程序
│       ├── config.py           # 配置管理
│       ├── handlers.py         # 消息处理器
│       ├── ai_adapter.py       # AI 引擎适配器
│       └── README.md           # 使用说明
├── requirements.txt            # Python 依赖
└── .env.example               # 环境变量示例
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写配置
```

### 3. 启动 Bot

```bash
python integrations/telegram/bot.py
```

## 🔧 配置说明

### 必需配置

```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# 管理员 Chat ID
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
```

### 可选配置

```bash
# AI 引擎选择（openai/claude/deepseek/ollama）
AI_ENGINE=openai

# OpenAI 配置
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4

# Claude 配置
CLAUDE_API_KEY=your_key
CLAUDE_MODEL=claude-sonnet-4

# DeepSeek 配置
DEEPSEEK_API_KEY=your_key
DEEPSEEK_MODEL=deepseek-chat

# Ollama 配置（本地）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## 📝 AI 引擎适配器

### 接口定义

```python
class AIAdapter:
    """AI 引擎适配器基类"""
    
    async def get_response(self, message: str, context: dict) -> str:
        """
        获取 AI 回复
        
        Args:
            message: 用户消息
            context: 上下文信息（用户ID、历史等）
            
        Returns:
            AI 回复内容
        """
        raise NotImplementedError
```

### 实现示例

```python
class OpenAIAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def get_response(self, message: str, context: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
```

## 🔌 集成到 Agent 系统

### 消息格式

```python
{
    "from": "telegram:user_id",
    "to": "agent:main",
    "type": "text",
    "content": "用户消息",
    "timestamp": 1234567890,
    "metadata": {
        "chat_id": 123456,
        "username": "user",
        "first_name": "User"
    }
}
```

### Agent 通信

```python
# 发送消息到 Agent
await send_to_agent(
    agent_id="agent:main",
    message=formatted_message
)

# 接收 Agent 回复
response = await receive_from_agent(agent_id="agent:main")

# 发送回 Telegram
await bot.send_message(chat_id, response)
```

## 🎨 自定义功能

### 添加命令

```python
@bot.command("custom")
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自定义命令"""
    await update.message.reply_text("自定义功能")
```

### 添加消息处理器

```python
@bot.message_handler(filters.PHOTO)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理图片消息"""
    # 下载图片
    # 调用 AI 分析
    # 返回结果
```

## 📊 监控和日志

### 日志配置

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
```

### 性能监控

```python
# 记录响应时间
start_time = time.time()
response = await ai_adapter.get_response(message)
duration = time.time() - start_time

logger.info(f"AI response time: {duration:.2f}s")
```

## 🔒 安全建议

1. **Token 保密**
   - 不要提交到 Git
   - 使用环境变量
   - 定期轮换

2. **访问控制**
   - 白名单机制
   - 速率限制
   - 权限验证

3. **数据安全**
   - 加密敏感信息
   - 定期清理日志
   - 遵守隐私政策

## 🐛 故障排查

### Bot 不响应

1. 检查 Token 是否正确
2. 检查网络连接（是否需要代理）
3. 查看日志错误信息

### AI 调用失败

1. 检查 API Key 是否有效
2. 确认账户余额充足
3. 检查 API 限流

### 消息发送失败

1. 检查 Chat ID 是否正确
2. 确认 Bot 有发送权限
3. 检查消息格式是否合法

## 📚 参考资源

- Telegram Bot API: https://core.telegram.org/bots/api
- python-telegram-bot: https://python-telegram-bot.org/
- smart-agent-template: https://gitee.com/sihj/smart-agent-template

---

**版本**: v1.0.0  
**更新日期**: 2026-03-28  
**适用场景**: 多渠道 Agent 通信、智能对话
