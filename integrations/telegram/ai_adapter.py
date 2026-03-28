"""
AI 引擎适配器
支持多种 AI 引擎的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional


class AIAdapter(ABC):
    """AI 引擎适配器基类"""
    
    @abstractmethod
    async def get_response(self, message: str, context: dict) -> str:
        """
        获取 AI 回复
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Returns:
            AI 回复内容
        """
        pass


class OpenAIAdapter(AIAdapter):
    """OpenAI 适配器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


class ClaudeAdapter(AIAdapter):
    """Claude 适配器"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4"):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")
    
    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system="你是一个智能助手",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return response.content[0].text


class DeepSeekAdapter(AIAdapter):
    """DeepSeek 适配器"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            self.model = model
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


class OllamaAdapter(AIAdapter):
    """Ollama 适配器（本地模型）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"  # Ollama 不需要真实 API key
            )
            self.model = model
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


def create_ai_adapter(engine: str, api_key: Optional[str] = None, 
                     model: Optional[str] = None, 
                     base_url: Optional[str] = None) -> AIAdapter:
    """
    创建 AI 适配器工厂函数
    
    Args:
        engine: AI 引擎类型
        api_key: API Key
        model: 模型名称
        base_url: API 基础 URL
        
    Returns:
        AI 适配器实例
    """
    if engine == "openai":
        return OpenAIAdapter(api_key, model or "gpt-4")
    elif engine == "claude":
        return ClaudeAdapter(api_key, model or "claude-sonnet-4")
    elif engine == "deepseek":
        return DeepSeekAdapter(api_key, model or "deepseek-chat")
    elif engine == "ollama":
        return OllamaAdapter(base_url or "http://localhost:11434", model or "llama2")
    else:
        raise ValueError(f"Unsupported AI engine: {engine}")
