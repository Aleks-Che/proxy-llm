from openai import AsyncOpenAI
from config import Config

class LocalProvider:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key="dummy-key",  # Для локальной модели не нужен реальный ключ
            base_url="http://localhost:10003/v1"
        )
        self.model = "gpt-oss-120b"  # Имя модели из llama-server

    async def chat_completion(self, messages, **kwargs):
        # Фильтрация параметров для локальной модели
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **filtered_kwargs
        )
        return response