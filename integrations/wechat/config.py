"""
微信公众号 Bot 配置管理
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class WechatConfig:
    """微信公众号配置"""
    app_id: str
    app_secret: str
    token: str
    encoding_aes_key: Optional[str] = None  # 消息加密密钥（可选）


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
        self.wechat = WechatConfig(
            app_id=os.getenv('WECHAT_APP_ID', ''),
            app_secret=os.getenv('WECHAT_APP_SECRET', ''),
            token=os.getenv('WECHAT_TOKEN', ''),
            encoding_aes_key=os.getenv('WECHAT_ENCODING_AES_KEY')
        )

        engine = os.getenv('AI_ENGINE', 'openai')
        self.ai = AIConfig(
            engine=engine,
            api_key=os.getenv(f"{engine.upper()}_API_KEY"),
            model=os.getenv(f"{engine.upper()}_MODEL", 'gpt-4'),
            base_url=os.getenv(f"{engine.upper()}_BASE_URL")
        )

    def validate(self) -> bool:
        if not self.wechat.app_id:
            raise ValueError("WECHAT_APP_ID is required")
        if not self.wechat.app_secret:
            raise ValueError("WECHAT_APP_SECRET is required")
        if not self.wechat.token:
            raise ValueError("WECHAT_TOKEN is required")
        return True


config = Config()
