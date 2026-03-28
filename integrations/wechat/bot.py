"""
微信公众号 Bot 主程序
基于 Flask 的 Webhook 服务，支持对话历史记忆
"""

import json
import logging
import os
import sys
from flask import Flask, request, make_response

from config import config
from wechat_utils import verify_signature, parse_message, build_text_reply
from ai_adapter import create_ai_adapter

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 对话历史存储目录
HISTORY_DIR = os.path.join(os.path.dirname(__file__), 'chat_history')
os.makedirs(HISTORY_DIR, exist_ok=True)

# 最大历史轮数
MAX_HISTORY = 10

# 初始化 AI 适配器
ai_adapter = None


def get_ai_adapter():
    global ai_adapter
    if ai_adapter is None:
        ai_adapter = create_ai_adapter(
            engine=config.ai.engine,
            api_key=config.ai.api_key,
            model=config.ai.model,
            base_url=config.ai.base_url
        )
    return ai_adapter


def load_history(user_id: str) -> list:
    """加载用户对话历史"""
    path = os.path.join(HISTORY_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_history(user_id: str, history: list):
    """保存用户对话历史（最多保留 MAX_HISTORY 轮）"""
    # 每轮包含 user + assistant 两条，保留最近 N 轮
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]
    path = os.path.join(HISTORY_DIR, f"{user_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信消息入口"""

    # GET 请求：微信服务器验证
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')

        if verify_signature(config.wechat.token, signature, timestamp, nonce):
            logger.info("微信服务器验证成功")
            return echostr
        else:
            logger.warning("微信服务器验证失败")
            return 'Invalid signature', 403

    # POST 请求：处理用户消息
    if request.method == 'POST':
        xml_data = request.data.decode('utf-8')
        msg = parse_message(xml_data)

        msg_type = msg.get('MsgType', '')
        from_user = msg.get('FromUserName', '')
        to_user = msg.get('ToUserName', '')

        logger.info(f"收到消息 from={from_user} type={msg_type}")

        # 处理文本消息
        if msg_type == 'text':
            user_content = msg.get('Content', '').strip()

            # 清除历史命令
            if user_content in ['清除记忆', '清空记忆', '/clear', '/reset']:
                save_history(from_user, [])
                ai_response = "✅ 对话历史已清除，我们重新开始吧！"
            else:
                try:
                    adapter = get_ai_adapter()

                    # 加载历史对话
                    history = load_history(from_user)

                    # 追加用户消息
                    history.append({"role": "user", "content": user_content})

                    # 调用 AI（带历史上下文）
                    context = {
                        "user_id": from_user,
                        "platform": "wechat",
                        "history": history
                    }
                    ai_response = adapter.get_response_sync(user_content, context, history=history)

                    # 追加 AI 回复并保存
                    history.append({"role": "assistant", "content": ai_response})
                    save_history(from_user, history)

                except Exception as e:
                    logger.error(f"AI 调用失败: {e}")
                    ai_response = "抱歉，我暂时无法回复，请稍后再试。"

            reply_xml = build_text_reply(from_user, to_user, ai_response)
            response = make_response(reply_xml)
            response.content_type = 'application/xml'
            return response

        # 关注事件
        elif msg_type == 'event':
            event = msg.get('Event', '')
            if event == 'subscribe':
                reply = build_text_reply(
                    from_user, to_user,
                    "👋 欢迎关注！\n\n我是 Smart Agent Bot，由 Claude AI 驱动。\n\n我会记住我们的对话历史，你可以随时继续之前的话题。\n\n发送「清除记忆」可以重置对话历史。"
                )
                response = make_response(reply)
                response.content_type = 'application/xml'
                return response

        return 'success'


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 微信公众号 Bot 启动（带记忆版）")
    print("=" * 60)

    try:
        config.validate()
        print(f"✅ 配置验证通过")
        print(f"🤖 AI 引擎: {config.ai.engine} / {config.ai.model}")
        print(f"🧠 对话历史: 最多保留 {MAX_HISTORY} 轮")
        print(f"📁 历史存储: {HISTORY_DIR}")
        print("=" * 60)
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)

    app.run(host='0.0.0.0', port=5001, debug=False)
