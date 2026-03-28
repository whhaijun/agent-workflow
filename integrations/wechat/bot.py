#!/usr/bin/env python3
"""
微信公众号 Bot 主程序（三层记忆版）
- 第一层：短期记忆（最近5轮，防崩溃）
- 第二层：长期记忆（AI自动摘要，不丢失）
- 第三层：结构化 System Prompt（准确理解上下文）
"""

import logging
import sys
from flask import Flask, request, make_response

from config import config
from wechat_utils import verify_signature, parse_message, build_text_reply
from ai_adapter import create_ai_adapter

# 导入记忆管理器
sys.path.insert(0, '..')
from memory_manager import MemoryManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化 AI 适配器
ai_adapter = None

# 初始化记忆管理器（延迟初始化，等 AI 适配器就绪）
memory_manager = None


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


def get_memory_manager():
    global memory_manager
    if memory_manager is None:
        adapter = get_ai_adapter()
        # 获取底层 AI 客户端用于压缩
        ai_client = getattr(adapter, 'client', None)
        memory_manager = MemoryManager(
            storage_dir='./chat_memory',
            ai_client=ai_client,
            ai_model=config.ai.model
        )
    return memory_manager


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信消息入口"""

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

    if request.method == 'POST':
        xml_data = request.data.decode('utf-8')
        msg = parse_message(xml_data)

        msg_type = msg.get('MsgType', '')
        from_user = msg.get('FromUserName', '')
        to_user = msg.get('ToUserName', '')

        logger.info(f"收到消息 from={from_user} type={msg_type}")

        if msg_type == 'text':
            user_content = msg.get('Content', '').strip()
            mm = get_memory_manager()

            # 清除记忆命令
            if user_content in ['清除记忆', '清空记忆', '/clear', '/reset']:
                mm.clear(from_user)
                ai_response = "✅ 记忆已清除，重新开始！"
            else:
                try:
                    adapter = get_ai_adapter()

                    # 使用记忆管理器处理消息
                    def ai_call(system, messages):
                        return adapter.get_response_sync(
                            messages[-1]['content'],
                            {"user_id": from_user},
                            history=messages,
                            system=system
                        )

                    ai_response = mm.process_message(
                        user_id=from_user,
                        user_message=user_content,
                        ai_call_fn=ai_call,
                        base_prompt="你是一个智能助手，回答简洁友好，记住用户的偏好和上下文。"
                    )

                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    ai_response = "抱歉，处理出错了，请稍后再试。"

            reply_xml = build_text_reply(from_user, to_user, ai_response)
            response = make_response(reply_xml)
            response.content_type = 'application/xml'
            return response

        elif msg_type == 'event':
            event = msg.get('Event', '')
            if event == 'subscribe':
                reply = build_text_reply(
                    from_user, to_user,
                    "👋 欢迎关注！\n\n我是 Smart Agent Bot，由 Claude AI 驱动。\n\n✅ 我会记住我们的对话\n✅ 重要信息永久保存\n✅ 跨对话保持上下文\n\n发送「清除记忆」可重置。"
                )
                response = make_response(reply)
                response.content_type = 'application/xml'
                return response

        return 'success'


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 微信公众号 Bot（三层记忆版）")
    print("=" * 60)

    try:
        config.validate()
        print(f"✅ 配置验证通过")
        print(f"🤖 AI 引擎: {config.ai.engine} / {config.ai.model}")
        print(f"🧠 短期记忆: {5} 轮")
        print(f"💾 长期记忆: AI 自动摘要压缩")
        print("=" * 60)
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)

    app.run(host='0.0.0.0', port=5001, debug=False)
