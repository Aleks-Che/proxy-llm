from openai import AsyncOpenAI
import asyncio
from config import config as Config

class MoonshotProvider:
    def __init__(self):
        # Получаем base_url из конфигурации
        moonshot_config = Config.get_provider_config("moonshot")
        base_url = moonshot_config.get("base_url", "https://api.moonshot.ai/v1")
        
        self.client = AsyncOpenAI(
            api_key=Config.MOONSHOT_API_KEY,
            base_url=base_url
        )
        self.model = Config.MOONSHOT_MODEL

    async def chat_completion(self, messages, **kwargs):
        # Filter out unsupported parameters for Moonshot
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}

        # Убираем None значения, которые могут вызвать ошибку by_alias
        filtered_kwargs = {k: v for k, v in filtered_kwargs.items() if v is not None}
        
        # Специальная обработка для модели kimi-k2.5, которая поддерживает только temperature=1
        if self.model == "kimi-k2.5" and "temperature" in filtered_kwargs:
            # Если передано temperature отличное от 1, либо убираем, либо устанавливаем 1
            if filtered_kwargs["temperature"] != 1.0:
                print(f"Warning: Model {self.model} only supports temperature=1. Using temperature=1 instead of {filtered_kwargs['temperature']}")
                filtered_kwargs["temperature"] = 1.0
        
        # Создаем базовый запрос
        request_data = {
            "model": self.model,
            "messages": messages
        }
        
        # Добавляем только те параметры, которые есть
        for param in supported_params:
            if param in filtered_kwargs:
                request_data[param] = filtered_kwargs[param]
        
        try:
            response = await self.client.chat.completions.create(**request_data)
            return response
        except Exception as e:
            # Логируем ошибку для диагностики
            print(f"Moonshot API error: {e}")
            raise