"""
Telegram Bot 消息处理器（优化版 v2.0）
新增：上下文感知、自我学习、工作规范融入
"""

import logging
import os
import sys
from telegram import Update
from telegram.ext import ContextTypes

# 添加父目录到路径，以便导入 memory_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_manager import MemoryManager

from .ai_adapter import AIAdapter

logger = logging.getLogger(__name__)


class MessageHandlers:
    """消息处理器集合（优化版）"""
    
    def __init__(self, ai_adapter: AIAdapter, storage_dir: str = "./data/memory"):
        self.ai_adapter = ai_adapter
        # 初始化记忆管理器
        self.memory = MemoryManager(
            storage_dir=storage_dir,
            ai_client=ai_adapter,  # 复用 AI 客户端
            ai_model=ai_adapter.model
        )
        logger.info(f"Memory manager initialized: {storage_dir}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        user_id = str(user.id)
        
        # 加载用户记忆
        memory_text = self.memory.load_memory(user_id)
        memory_hint = ""
        if memory_text:
            memory_hint = "\n\n💡 我记得你，让我们继续之前的对话吧！"
        
        welcome_message = f"""
👋 你好 {user.first_name}！

我是 Smart Agent Bot，一个智能助手。

可用命令：
/start - 开始使用
/help - 查看帮助
/status - 查看状态
/memory - 查看我对你的记忆

💬 直接发送消息，我会智能回复你！{memory_hint}
"""
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user_id} started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 帮助信息

我是一个智能助手，可以：
• 回答各种问题
• 提供技术建议
• 帮助解决问题
• 进行自然对话
• 记住我们的对话历史
• 从你的纠正中学习

💡 使用方法：
直接发送消息给我，我会智能回复。

🧠 记忆能力：
• 短期记忆：最近 5 轮对话
• 长期记忆：自动压缩保存
• 自我学习：记住你的纠正

🤖 基于 smart-agent-template 构建
"""
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        user_id = str(update.effective_user.id)
        
        # 获取记忆统计
        history = self.memory.load_history(user_id)
        memory_text = self.memory.load_memory(user_id)
        
        status_text = f"""
✅ 系统状态

• Bot 状态: 运行中
• AI 引擎: 已连接
• 版本: v2.0.0

🧠 你的记忆状态：
• 短期记忆：{len(history)} 条消息
• 长期记忆：{len(memory_text)} 字符
• 总对话轮数：{self.memory._get_total_rounds(user_id)}

一切正常！
"""
        await update.message.reply_text(status_text)
    
    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /memory 命令 - 查看记忆"""
        user_id = str(update.effective_user.id)
        memory_text = self.memory.load_memory(user_id)
        
        if not memory_text:
            await update.message.reply_text("🧠 我还没有关于你的长期记忆。让我们多聊聊吧！")
            return
        
        # 限制输出长度
        if len(memory_text) > 1000:
            memory_text = memory_text[:1000] + "\n\n... (更多内容已省略)"
        
        await update.message.reply_text(f"🧠 我对你的记忆：\n\n{memory_text}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通文本消息（优化版：上下文感知 + 自我学习）"""
        user = update.effective_user
        user_id = str(user.id)
        user_message = update.message.text
        
        logger.info(f"User {user_id} ({user.first_name}): {user_message}")
        
        # 发送"正在输入"状态
        await update.message.chat.send_action("typing")
        
        try:
            # 1. 加载记忆（上下文感知）
            history = self.memory.load_history(user_id)
            memory_text = self.memory.load_memory(user_id)
            
            # 2. 检测用户纠正（自我学习）
            correction_detected = self._detect_correction(user_message)
            if correction_detected:
                logger.info(f"Correction detected from user {user_id}")
                # 标记为学习内容
                user_message = f"[用户纠正] {user_message}"
            
            # 3. 构建增强上下文
            message_context = {
                "user_id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "chat_id": update.message.chat_id,
                "history": history,  # 短期记忆
                "memory": memory_text,  # 长期记忆
                "system_prompt": self._build_system_prompt()  # 工作规范
            }
            
            # 4. 调用 AI 获取回复
            ai_response = await self.ai_adapter.get_response(user_message, message_context)
            
            # 5. 保存对话到记忆
            self.memory.add_message(user_id, "user", user_message)
            self.memory.add_message(user_id, "assistant", ai_response)
            self.memory._increment_rounds(user_id)
            
            # 6. 异步压缩记忆（如果需要）
            if self.memory.should_compress(user_id):
                logger.info(f"Triggering memory compression for user {user_id}")
                self.memory.compress_async(user_id)
            
            # 7. 发送回复
            await update.message.reply_text(ai_response)
            
            logger.info(f"Bot replied to {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ 抱歉，处理消息时出错了。请稍后再试。"
            )
    
    def _detect_correction(self, message: str) -> bool:
        """检测用户纠正"""
        correction_keywords = [
            "不对", "不是", "错了", "应该是", "其实是",
            "不对，", "不是，", "错了，", "应该是", "其实是",
            "no,", "wrong", "actually", "should be", "it's"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in correction_keywords)
    
    def _build_system_prompt(self) -> str:
        """构建 System Prompt（融入工作规范）"""
        return """你是 Smart Agent Bot，一个智能助手。

【核心原则】
1. 3高原则：高质量 + 高效率 + 高节省
2. 第一性原理：从本质出发，找最简解法
3. 主动执行，不反复询问

【工作规范】
- 理解上下文：利用对话历史和长期记忆
- 自我学习：记住用户的纠正，下次不再犯错
- 简洁回复：直接给答案，不废话
- 承认不足：不知道就说不知道，不要编造

【记忆能力】
- 你有短期记忆（最近5轮对话）
- 你有长期记忆（自动压缩保存）
- 你会从用户纠正中学习

【回复风格】
- 友好、专业、简洁
- 用 emoji 增加亲和力
- 避免冗长的解释
"""
    
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
