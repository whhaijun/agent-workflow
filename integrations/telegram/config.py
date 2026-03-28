"""
Telegram Bot 配置管理
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramConfig:
    """Telegram Bot 配置"""
    bot_token: str
    admin_chat_id: int
    proxy_url: Optional[str] = None


@dataclass
class AIConfig:
    """AI 引擎配置"""
    engine: str  # openai, claude, deepseek, ollama
    api_key: Optional[str] = None
    model: str = "gpt-4"
    base_url: Optional[str] = None


class Config:
    """配置管理器"""
    
    def __init__(self):
        self.telegram = TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            admin_chat_id=int(os.getenv('TELEGRAM_ADMIN_CHAT_ID', '0')),
            proxy_url=os.getenv('TELEGRAM_PROXY_URL')
        )
        
        self.ai = AIConfig(
            engine=os.getenv('AI_ENGINE', 'openai'),
            api_key=os.getenv(f"{os.getenv('AI_ENGINE', 'openai').upper()}_API_KEY"),
            model=os.getenv(f"{os.getenv('AI_ENGINE', 'openai').upper()}_MODEL", 'gpt-4'),
            base_url=os.getenv(f"{os.getenv('AI_ENGINE', 'openai').upper()}_BASE_URL")
        )
    
    def validate(self) -> bool:
        """验证配置"""
        if not self.telegram.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if not self.telegram.admin_chat_id:
            raise ValueError("TELEGRAM_ADMIN_CHAT_ID is required")
        
        if self.ai.engine not in ['openai', 'claude', 'deepseek', 'ollama']:
            raise ValueError(f"Unsupported AI engine: {self.ai.engine}")
        
        return True


# 全局配置实例
config = Config()
