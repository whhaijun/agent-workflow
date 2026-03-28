"""
AI 引擎适配器（微信版）
复用 Telegram 适配器，增加同步调用方法
微信 Webhook 需要同步响应，不能用 async
"""

import asyncio
from typing import Optional


class AIAdapter:
    """AI 引擎适配器基类"""

    def get_response_sync(self, message: str, context: dict) -> str:
        """同步调用（微信 Webhook 使用）"""
        return asyncio.run(self.get_response(message, context))

    async def get_response(self, message: str, context: dict) -> str:
        raise NotImplementedError


class OpenAIAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        try:
            from openai import AsyncOpenAI
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = AsyncOpenAI(**kwargs)
            self.model = model
        except ImportError:
            raise ImportError("请安装: pip install openai")

    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手，请用简洁友好的方式回复。"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


class ClaudeAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4", base_url: Optional[str] = None):
        try:
            import anthropic
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = anthropic.AsyncAnthropic(**kwargs)
            self.model = model
        except ImportError:
            raise ImportError("请安装: pip install anthropic")

    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system="你是一个智能助手，请用简洁友好的方式回复。",
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text


class DeepSeekAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            self.model = model
        except ImportError:
            raise ImportError("请安装: pip install openai")

    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手，请用简洁友好的方式回复。"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


class OllamaAdapter(AIAdapter):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"
            )
            self.model = model
        except ImportError:
            raise ImportError("请安装: pip install openai")

    async def get_response(self, message: str, context: dict) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个智能助手，请用简洁友好的方式回复。"},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content


def create_ai_adapter(engine: str, api_key: Optional[str] = None,
                      model: Optional[str] = None,
                      base_url: Optional[str] = None) -> AIAdapter:
    if engine == "openai":
        return OpenAIAdapter(api_key, model or "gpt-4", base_url)
    elif engine == "claude":
        return ClaudeAdapter(api_key, model or "claude-sonnet-4", base_url)
    elif engine == "deepseek":
        return DeepSeekAdapter(api_key, model or "deepseek-chat")
    elif engine == "ollama":
        return OllamaAdapter(base_url or "http://localhost:11434", model or "llama2")
    else:
        raise ValueError(f"不支持的 AI 引擎: {engine}")
