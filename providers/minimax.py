import anthropic
import asyncio
from config import config as Config
import time
from typing import AsyncGenerator, Dict, Any
import types


class MiniMaxProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("minimax")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://api.minimax.io/anthropic")
        # Anthropic client with custom base URL
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        # Получаем первую модель из настроек
        models = provider_config.get("models", [])
        self.model = models[0]["name"] if models else "MiniMax-M2.1"
    
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
        # Convert messages format from OpenAI to Anthropic format
        # Anthropic expects list of dicts with role and content
        # MiniMax likely uses same format as Anthropic
        system = None
        if messages and messages[0].get("role") == "system":
            system = messages[0].get("content")
            messages = messages[1:]
        
        # Filter out unsupported parameters for Anthropic/MiniMax
        supported_params = ['temperature', 'max_tokens', 'stream', 'top_p', 'stop', 'thinking']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}
        
        # Prepare messages for Anthropic API
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(content, list):
                # Handle multimodal content
                content = [item for item in content if item.get("type") == "text"]
                if content:
                    content = content[0].get("text", "")
                else:
                    content = ""
            anthropic_messages.append({
                "role": role,
                "content": content
            })
        
        # Handle streaming
        stream = filtered_kwargs.pop('stream', False)
        if stream:
            # Return an async generator for streaming
            return self._stream_response(system, anthropic_messages, filtered_kwargs)
        else:
            # Non-streaming
            response = self.client.messages.create(
                model=self.model,
                system=system,
                messages=anthropic_messages,
                **filtered_kwargs
            )
            return self._format_non_stream_response(response)

    async def _stream_response(self, system, anthropic_messages, filtered_kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield chunks in OpenAI-compatible format from Anthropic stream."""
        # We'll run the synchronous stream in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Create a queue to pass events from sync thread to async generator
        queue = asyncio.Queue()
        
        def iterate_stream():
            with self.client.messages.stream(
                model=self.model,
                system=system,
                messages=anthropic_messages,
                **filtered_kwargs
            ) as stream:
                for event in stream:
                    # Put event into queue
                    asyncio.run_coroutine_threadsafe(queue.put(event), loop)
                # Signal end of stream
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
        
        # Start the sync iteration in a separate thread
        stream_thread = loop.run_in_executor(None, iterate_stream)
        
        try:
            while True:
                event = await queue.get()
                if event is None:
                    # End of stream
                    break
                
                # Process event and yield appropriate chunk
                chunk = self._event_to_chunk(event)
                if chunk is not None:
                    yield chunk
        finally:
            # Ensure thread is cleaned up
            stream_thread.cancel()

    def _event_to_chunk(self, event):
        """Convert Anthropic stream event to OpenAI-compatible chunk."""
        event_type = event.type
        
        # We only care about text deltas for content
        if event_type == "content_block_delta":
            delta = event.delta
            if delta.type == "text_delta":
                # Create a chunk with text content
                chunk_dict = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": delta.text,
                                "reasoning_content": None
                            },
                            "finish_reason": None
                        }
                    ]
                }
                return self._MockChunk(chunk_dict)
            elif delta.type == "thinking_delta":
                # Thinking block - we can include as reasoning_content if needed
                # For now, ignore or include as reasoning_content
                pass
        elif event_type == "message_stop":
            # Final chunk with finish reason
            chunk_dict = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            return self._MockChunk(chunk_dict)
        return None

    def _format_non_stream_response(self, response):
        """Convert Anthropic non-streaming response to OpenAI format."""
        # Extract text content and thinking blocks
        text_parts = []
        thinking_content = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "thinking":
                thinking_content.append(block.thinking)
        
        text_content = "".join(text_parts) if text_parts else ""
        
        # If no text content but there is at least one block, try to extract text from any block
        if not text_content and response.content:
            for block in response.content:
                if hasattr(block, 'text'):
                    text_content = block.text
                    break
        
        choice = {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": text_content
            },
            "finish_reason": response.stop_reason
        }
        
        # Include thinking blocks in response if present
        extra = {}
        if thinking_content:
            extra['thinking'] = thinking_content
        
        # Create a dictionary representation
        result_dict = {
            "id": response.id,
            "object": "chat.completion",
            "created": int(time.time()),  # fallback timestamp
            "model": response.model,
            "choices": [choice],
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            **extra
        }
        
        # Convert to an object with attributes and model_dump method
        class MockResponse:
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
        
        return MockResponse(result_dict)