from openai import AsyncOpenAI
import asyncio
from config import Config

class DeepSeekProvider:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model = Config.DEEPSEEK_MODEL

    async def chat_completion(self, messages, **kwargs):
        # Filter out unsupported parameters for DeepSeek
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **filtered_kwargs
        )
        return response