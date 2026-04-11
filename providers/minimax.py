from openai import AsyncOpenAI
import asyncio
from config import config as Config
import time
from typing import AsyncGenerator, Dict, Any


class MiniMaxProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("minimax")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://api.minimax.io/v1")
        # OpenAI-compatible client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        # Get first model from settings
        models = provider_config.get("models", [])
        self.model = models[0]["name"] if models else "MiniMax-M2.7"
    
    class _MockChunk:
        """Mock chunk object with attributes and model_dump method."""
        def __init__(self, data):
            self._data = data
            for key, value in data.items():
                setattr(self, key, value)
        
        def model_dump(self):
            return self._data
        
        def to_dict(self):
            return self._data
        
        def dict(self):
            return self._data

    async def chat_completion(self, messages, **kwargs):
        # Extract system message if present (OpenAI format supports system role)
        # MiniMax likely supports system role directly, but we keep compatibility
        system = None
        if messages and messages[0].get("role") == "system":
            system = messages[0].get("content")
            messages = messages[1:]
        
        # Filter out unsupported parameters for MiniMax (OpenAI-compatible)
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 'thinking', 'tools', 'tool_choice']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}
        
        # Handle streaming
        stream = filtered_kwargs.pop('stream', False)
        
        # Auto-enable streaming for large max_tokens (optional)
        max_tokens = filtered_kwargs.get('max_tokens', 4096)
        if max_tokens > 100000 and not stream:
            stream = True
            print(f"Auto-enabling streaming for large max_tokens ({max_tokens})")
        
        # Prepare messages for API (include system as a message with role "system" if needed)
        api_messages = messages
        if system:
            # Insert system message at the beginning
            api_messages = [{"role": "system", "content": system}] + messages
        
        if stream:
            # Return an async generator for streaming
            return self._stream_response(api_messages, filtered_kwargs)
        else:
            # Non-streaming
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                **filtered_kwargs
            )
            return response

    async def _stream_response(self, messages, filtered_kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield chunks in OpenAI-compatible format from MiniMax stream."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **filtered_kwargs
        )
        
        async for chunk in stream:
            yield chunk