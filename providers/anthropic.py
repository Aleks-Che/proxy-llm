from openai import AsyncOpenAI
import asyncio
from config import config as Config

class AnthropicProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("anthropic")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://api.anthropic.com/v1")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        # Получаем первую модель из настроек
        models = provider_config.get("models", [])
        self.model = models[0].get("name", "claude-opus-4-1-20250805") if models else "claude-opus-4-1-20250805"

    async def chat_completion(self, messages, **kwargs):
        # Filter out unsupported parameters for Anthropic
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **filtered_kwargs
        )
        return response