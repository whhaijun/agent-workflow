# 微信公众号 Bot 集成指南

## 📋 概述

基于微信公众号 Webhook 的智能 Bot，支持多种 AI 引擎。

## 📁 文件结构

```
integrations/wechat/
├── bot.py              # Flask Webhook 主程序
├── config.py           # 配置管理
├── wechat_utils.py     # 微信工具函数（签名验证、XML 解析）
├── ai_adapter.py       # AI 引擎适配器
├── .env.example        # 配置示例（可提交）
└── README.md           # 本文档
```

## 🚀 快速开始

### 第 1 步：注册微信公众号

1. 访问：https://mp.weixin.qq.com/
2. 注册订阅号（个人可注册）
3. 进入「设置与开发」→「基本配置」
4. 获取 AppID 和 AppSecret
5. 设置 Token（自定义字符串）

### 第 2 步：安装依赖

```bash
pip install flask
pip install openai      # 如果使用 OpenAI/DeepSeek
pip install anthropic   # 如果使用 Claude
```

### 第 3 步：配置环境变量

```bash
cp .env.example .env.local
# 编辑 .env.local，填写真实配置
```

### 第 4 步：启动服务

```bash
cd integrations/wechat
set -a && source .env.local && set +a
python bot.py
```

服务启动在 `http://0.0.0.0:5000`

### 第 5 步：配置 Webhook

**重要：微信需要公网可访问的 HTTPS 地址**

本地开发推荐使用 ngrok：
```bash
# 安装 ngrok
brew install ngrok

# 暴露本地端口
ngrok http 5000
# 获得类似：https://xxxx.ngrok.io
```

在微信公众号后台：
1. 「设置与开发」→「基本配置」→「服务器配置」
2. 填写 URL：`https://xxxx.ngrok.io/wechat`
3. 填写 Token（与 .env.local 中一致）
4. 点击「提交」验证

---

## 🔧 配置说明

### 微信公众号配置

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| WECHAT_APP_ID | 公众号 AppID | 微信公众号后台 |
| WECHAT_APP_SECRET | 公众号 AppSecret | 微信公众号后台 |
| WECHAT_TOKEN | 自定义 Token | 自己设置，与后台一致 |

### AI 引擎配置

```bash
# 使用 DeepSeek（国内推荐，便宜）
AI_ENGINE=deepseek
DEEPSEEK_API_KEY=your_key

# 使用 Ollama（本地免费）
AI_ENGINE=ollama
OLLAMA_MODEL=llama2

# 使用 Claude
AI_ENGINE=claude
CLAUDE_API_KEY=your_key
CLAUDE_BASE_URL=http://your_server:3200  # 自定义服务
```

---

## ⚠️ 重要限制

| 限制 | 说明 |
|------|------|
| 响应时间 | 必须在 5 秒内回复，否则微信认为超时 |
| 主动推送 | 只能在用户 48 小时内互动后推送 |
| HTTPS | Webhook 必须是 HTTPS |
| 消息类型 | 当前支持文本消息和关注事件 |

---

## 🔒 安全注意事项

- `.env.local` 已加入 `.gitignore`，不会提交
- AppSecret 是敏感信息，不要泄露
- Token 用于验证微信服务器，保持私密

---

## 📚 参考资源

- 微信公众号开发文档：https://developers.weixin.qq.com/doc/offiaccount/
- Flask 文档：https://flask.palletsprojects.com/

---

**版本**: v1.0.0  
**更新日期**: 2026-03-28
