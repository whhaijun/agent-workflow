# 微信公众号 Bot 快速接入指南（最简版）

> 目标：从零到收到微信消息，最快 15 分钟完成

---

## 前置准备（一次性）

### 1. 注册微信测试号（2分钟）

1. 打开：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
2. 微信扫码登录
3. 记录页面上的 **appID** 和 **appsecret**

### 2. 安装依赖（1分钟）

```bash
pip3 install flask
npm install -g localtunnel
```

---

## 启动流程（每次启动执行）

### 第 1 步：创建本地配置

```bash
cd ~/Desktop/smart-agent-template/integrations/wechat

cat > .env.local << 'EOF'
WECHAT_APP_ID=你的appID
WECHAT_APP_SECRET=你的appsecret
WECHAT_TOKEN=smartbot2026
AI_ENGINE=openai
OPENAI_API_KEY=你的API_Key
OPENAI_BASE_URL=你的服务地址/v1
OPENAI_MODEL=你的模型名
EOF
```

### 第 2 步：启动 Flask 服务（新终端）

```bash
cd ~/Desktop/smart-agent-template/integrations/wechat
set -a && source .env.local && set +a
python3 bot.py
```

看到 `Running on http://0.0.0.0:5001` 表示成功。

### 第 3 步：启动内网穿透（新终端）

```bash
lt --port 5001 --subdomain smartagentbot
```

看到 `your url is: https://smartagentbot.loca.lt` 表示成功。

### 第 4 步：配置微信测试号（只需配置一次）

1. 打开：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
2. 找到「接口配置信息」
3. 填写：
   - **URL**：`https://smartagentbot.loca.lt/wechat`
   - **Token**：`smartbot2026`
4. 点击「提交」→ 显示「配置成功」

### 第 5 步：测试

1. 用微信扫描测试号二维码关注
2. 发送任意消息
3. Bot 自动回复

---

## 切换 AI 引擎

编辑 `.env.local`，修改以下配置：

**使用本地 OpenAI 兼容服务：**
```bash
AI_ENGINE=openai
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=http://192.168.x.x:端口/v1
OPENAI_MODEL=模型名称
```

**使用 Claude（OpenClaw 配置）：**
```bash
AI_ENGINE=claude
CLAUDE_API_KEY=cr_xxx
CLAUDE_BASE_URL=http://192.168.1.99:3200
CLAUDE_MODEL=claude-sonnet-4-6
```

**使用 DeepSeek：**
```bash
AI_ENGINE=deepseek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat
```

修改后重启 Flask 服务即可。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 配置失败 | ngrok 被微信屏蔽 | 改用 localtunnel |
| 消息无回复 | Flask 服务未启动 | 检查终端是否在运行 |
| localtunnel 断开 | 网络不稳定 | 重新运行 `lt --port 5001` |
| 5001 端口占用 | 其他程序占用 | 改用 5002，同步修改 lt 命令 |

---

## 注意事项

- ⚠️ `.env.local` 包含敏感信息，不要提交到 Git
- ⚠️ localtunnel 每次重启 URL 不变（固定 subdomain）
- ⚠️ 微信测试号 URL 配置一次即可，不需要每次重新配置
- ⚠️ Flask 和 localtunnel 需要同时运行

---

**更新日期**: 2026-03-28  
**测试状态**: ✅ 已验证可用
