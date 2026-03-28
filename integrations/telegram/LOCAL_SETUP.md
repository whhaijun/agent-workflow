# 本地开发指南

## ⚠️ 重要提示

本文档包含本地开发配置，**不要提交到 Git**。

## 🔑 获取 Claude API Key

### 方式 1：从 OpenClaw 配置读取

如果你已经在使用 OpenClaw（就像现在和我对话），API Key 已经配置好了。

查看配置：
```bash
# 查看 OpenClaw 配置目录
ls ~/.openclaw/

# 或者查看环境变量
env | grep ANTHROPIC
```

### 方式 2：从 Anthropic 官网获取

1. 访问：https://console.anthropic.com/
2. 登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制保存

## 📝 配置步骤

### 1. 创建本地配置文件

```bash
cd ~/Desktop/smart-agent-template/integrations/telegram

# 复制示例配置
cp .env.local.example .env.local

# 编辑配置
nano .env.local
```

### 2. 填写配置

编辑 `.env.local`：

```bash
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=8617657397:AAEqcEphNdIPBN0ENveku94fjEwX8Ft8yvs
TELEGRAM_ADMIN_CHAT_ID=7420831199

# AI 引擎配置
AI_ENGINE=claude

# Claude API 配置
CLAUDE_API_KEY=sk-ant-api03-你的真实API_Key
CLAUDE_MODEL=claude-sonnet-4

# 代理配置
http_proxy=http://127.0.0.1:6152
https_proxy=http://127.0.0.1:6152
```

### 3. 启动 Bot

```bash
./start_local.sh
```

## 🔒 安全注意事项

1. **不要提交 .env.local**
   - 已添加到 .gitignore
   - 包含敏感的 API Key

2. **不要提交 start_local.sh**
   - 包含本地配置逻辑
   - 已添加到 .gitignore

3. **不要在代码中硬编码 API Key**
   - 始终使用环境变量
   - 使用 .env.local 文件

## 📊 验证配置

### 测试 Claude API

```bash
# 使用 curl 测试
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 测试 Bot

1. 启动 Bot：`./start_local.sh`
2. 打开 Telegram
3. 搜索 `@WftOpenClaw_bot`
4. 发送消息测试

## 🐛 故障排查

### API Key 无效

```bash
# 检查 API Key 格式
echo $CLAUDE_API_KEY | wc -c
# 应该是 100+ 字符

# 检查 API Key 是否有效
curl -I https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY"
```

### 网络连接失败

```bash
# 检查代理
curl -x http://127.0.0.1:6152 https://api.anthropic.com

# 检查 Surge 是否运行
ps aux | grep Surge
```

## 📚 相关文档

- Claude API 文档：https://docs.anthropic.com/
- Telegram Bot API：https://core.telegram.org/bots/api
- smart-agent-template：https://gitee.com/sihj/smart-agent-template

---

**⚠️ 再次提醒：此文件包含敏感配置，不要提交到 Git！**
