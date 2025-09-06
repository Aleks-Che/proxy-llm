from openai import AsyncOpenAI
import asyncio
import aiohttp
import json
from config import config as Config
import logging

logger = logging.getLogger(__name__)

class OpenRouterProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("openrouter")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://openrouter.ai/api/v1")
        self.default_headers = {
            "HTTP-Referer": "https://github.com/RooVetGit/Roo-Code",
            "X-Title": "Roo Code",
            "User-Agent": "RooCode/1.0.0"
        }
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.default_headers
        )
        # Получаем первую модель из настроек
        models = provider_config.get("models", [])
        self.model = models[0]["name"] if models else "anthropic/claude-sonnet-4"

    async def get_models(self):
        """Получить список доступных моделей от OpenRouter"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}", **self.default_headers}
                async with session.get(f"{self.base_url}/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.error(f"Failed to fetch models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    async def chat_completion(self, messages, **kwargs):
        # Поддерживаемые параметры для OpenRouter
        supported_params = [
            'temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty',
            'presence_penalty', 'stop', 'transforms', 'provider', 'reasoning'
        ]
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}

        # Добавляем stream_options если stream=True
        if filtered_kwargs.get('stream', False):
            filtered_kwargs['stream_options'] = {'include_usage': True}

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **filtered_kwargs
            )
            return response
        except Exception as e:
            logger.error(f"OpenRouter chat completion error: {e}")
            raise