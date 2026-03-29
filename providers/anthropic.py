import anthropic
import asyncio
from config import config as Config
from typing import Dict, Any, Optional


class AnthropicProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("anthropic")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://api.anthropic.com/v1")
        
        # Используем нативный Anthropic клиент
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.async_client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Получаем первую модель из настроек
        models = provider_config.get("models", [])
        self.model = models[0]["name"] if models else "claude-opus-4-1-20250805"

    async def chat_completion(self, messages, **kwargs):
        # Преобразуем сообщения из формата OpenAI в формат Anthropic
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Если это системное сообщение, сохраняем отдельно
            if role == "system":
                system_message = content
                continue
            
            # Преобразуем роль
            if role == "assistant":
                anthropic_role = "assistant"
            else:  # user, developer, tool
                anthropic_role = "user"
            
            anthropic_messages.append({
                "role": anthropic_role,
                "content": content
            })
        
        # Подготавливаем параметры
        params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        
        # Добавляем опциональные параметры
        if system_message:
            params["system"] = system_message
        
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        
        if "stream" in kwargs and kwargs["stream"]:
            # Для стриминга возвращаем async генератор
            params["stream"] = True
            return self._stream_completion(params)
        else:
            # Для нестриминговых запросов
            # Проверяем, не слишком ли большой max_tokens для нестримингового запроса
            max_tokens = params.get("max_tokens", 4096)
            if max_tokens > 100000:  # Порог для включения стриминга
                # Автоматически включаем стриминг для очень длинных запросов
                params["stream"] = True
                return self._stream_completion(params)
            
            # Обычный синхронный запрос
            response = await self.async_client.messages.create(**params)
            return self._format_response(response)

    async def _stream_completion(self, params):
        """Обработка стримингового ответа"""
        stream = await self.async_client.messages.create(**params)
        
        async def response_generator():
            async for event in stream:
                yield self._format_stream_event(event)
        
        return response_generator()

    def _format_response(self, response):
        """Форматирование ответа Anthropic в формат, совместимый с OpenAI"""
        # Создаем объект, похожий на OpenAI response
        class MockChoice:
            def __init__(self, content):
                class MockMessage:
                    def __init__(self, content):
                        self.content = content
                        self.role = "assistant"
                self.message = MockMessage(content)
                self.index = 0
                self.finish_reason = "stop"
        
        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
                self.model = self.model
                self.created = None
                self.id = None
        
        content = ""
        if hasattr(response, 'content'):
            for block in response.content:
                if block.type == 'text':
                    content += block.text
        
        mock_resp = MockResponse(content)
        mock_resp.model = self.model
        return mock_resp

    def _format_stream_event(self, event):
        """Форматирование стримингового события Anthropic в формат OpenAI"""
        class MockDelta:
            def __init__(self, content):
                self.content = content
        
        class MockChoice:
            def __init__(self, delta, finish_reason=None):
                self.delta = delta
                self.index = 0
                self.finish_reason = finish_reason
        
        class MockStreamEvent:
            def __init__(self, choices, model=None):
                self.choices = choices
                self.model = model
                self.created = None
                self.id = None
        
        if event.type == 'content_block_delta':
            # Текстовый чанк
            delta = MockDelta(event.delta.text)
            choice = MockChoice(delta)
            return MockStreamEvent([choice], self.model)
        elif event.type == 'message_stop':
            # Завершение сообщения
            delta = MockDelta("")
            choice = MockChoice(delta, finish_reason="stop")
            return MockStreamEvent([choice], self.model)
        else:
            # Другие события (игнорируем или возвращаем пустой delta)
            delta = MockDelta("")
            choice = MockChoice(delta)
            return MockStreamEvent([choice], self.model)