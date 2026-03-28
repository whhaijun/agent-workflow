"""
Telegram Bot 消息处理器
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from ai_adapter import AIAdapter

logger = logging.getLogger(__name__)


class MessageHandlers:
    """消息处理器集合"""
    
    def __init__(self, ai_adapter: AIAdapter):
        self.ai_adapter = ai_adapter
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        welcome_message = f"""
👋 你好 {user.first_name}！

我是 Smart Agent Bot，一个智能助手。

可用命令：
/start - 开始使用
/help - 查看帮助
/status - 查看状态

💬 直接发送消息，我会智能回复你！
"""
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 帮助信息

我是一个智能助手，可以：
• 回答各种问题
• 提供技术建议
• 帮助解决问题
• 进行自然对话

💡 使用方法：
直接发送消息给我，我会智能回复。

🤖 基于 smart-agent-template 构建
"""
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        status_text = """
✅ 系统状态

• Bot 状态: 运行中
• AI 引擎: 已连接
• 版本: v1.0.0

一切正常！
"""
        await update.message.reply_text(status_text)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通文本消息"""
        user = update.effective_user
        user_message = update.message.text
        
        logger.info(f"User {user.id} ({user.first_name}): {user_message}")
        
        # 发送"正在输入"状态
        await update.message.chat.send_action("typing")
        
        try:
            # 构建上下文
            message_context = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "chat_id": update.message.chat_id
            }
            
            # 调用 AI 获取回复
            ai_response = await self.ai_adapter.get_response(user_message, message_context)
            
            # 发送回复
            await update.message.reply_text(ai_response)
            
            logger.info(f"Bot replied to {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "❌ 抱歉，处理消息时出错了。请稍后再试。"
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片消息"""
        await update.message.reply_text(
            "📷 我看到你发了一张图片！目前我还不能分析图片内容，但未来会支持的。"
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文件消息"""
        file_name = update.message.document.file_name
        await update.message.reply_text(
            f"📄 收到文件: {file_name}\n目前我还不能处理文件，但未来会支持的。"
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理错误"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ 抱歉，处理消息时出错了。请稍后再试。"
            )
