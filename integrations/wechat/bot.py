#!/usr/bin/env python3
"""
微信公众号 Bot 主程序
基于 Flask 的 Webhook 服务
"""

import logging
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

        # 只处理文本消息
        if msg_type == 'text':
            user_content = msg.get('Content', '')
            try:
                adapter = get_ai_adapter()
                context = {"user_id": from_user, "platform": "wechat"}
                ai_response = adapter.get_response_sync(user_content, context)
            except Exception as e:
                logger.error(f"AI 调用失败: {e}")
                ai_response = "抱歉，我暂时无法回复，请稍后再试。"

            reply_xml = build_text_reply(from_user, to_user, ai_response)
            response = make_response(reply_xml)
            response.content_type = 'application/xml'
            return response

        # 其他消息类型
        elif msg_type == 'event':
            event = msg.get('Event', '')
            if event == 'subscribe':
                reply = build_text_reply(
                    from_user, to_user,
                    "👋 欢迎关注！\n\n我是 Smart Agent Bot，直接发消息给我，我会智能回复你！"
                )
                response = make_response(reply)
                response.content_type = 'application/xml'
                return response

        return 'success'


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 微信公众号 Bot 启动")
    print("=" * 60)

    try:
        config.validate()
        print(f"✅ 配置验证通过")
        print(f"🤖 AI 引擎: {config.ai.engine} / {config.ai.model}")
        print(f"🌐 Webhook 地址: http://your-server/wechat")
        print("=" * 60)
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)

    app.run(host='0.0.0.0', port=5000, debug=False)
