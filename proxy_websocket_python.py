#!/usr/bin/env python3
"""
Python WebSocket Proxy Client для закрытой сети
Создает постоянное соединение с WebSocket Bridge и проксирует HTTP запросы
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
import aiohttp_cors
import time
from dataclasses import dataclass, field
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Конфигурация WebSocket соединения"""
    url: str = "ws://localhost:8765"
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    connection_timeout: int = 30
    heartbeat_interval: int = 15


class WebSocketBridgeClient:
    """Клиент для подключения к WebSocket Bridge"""
    
    def __init__(self, config: WebSocketConnection):
        self.config = config
        self.websocket = None
        self.is_connected = False
        self.message_queue = []
        self.pending_requests = {}
        self.request_id = 0
        self.reconnect_attempts = 0
        
    async def connect(self):
        """Подключение к WebSocket Bridge"""
        while self.reconnect_attempts < self.config.max_reconnect_attempts:
            try:
                logger.info(f"Подключение к WebSocket Bridge: {self.config.url}")
                self.websocket = await websockets.connect(self.config.url)
                self.is_connected = True
                self.reconnect_attempts = 0
                logger.info("WebSocket соединение установлено")
                
                # Отправляем накопленные сообщения
                await self.flush_message_queue()
                
                # Запускаем обработку входящих сообщений
                await self.handle_messages()
                
            except Exception as e:
                logger.error(f"Ошибка подключения к WebSocket: {e}")
                self.is_connected = False
                self.reconnect_attempts += 1
                logger.info(f"Переподключение через {self.config.reconnect_interval}с (попытка {self.reconnect_attempts})")
                await asyncio.sleep(self.config.reconnect_interval)
    
    async def handle_messages(self):
        """Обработка входящих сообщений от WebSocket Bridge"""
        try:
            async for message in self.websocket:
                await self.process_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket соединение закрыто")
            self.is_connected = False
            await self.schedule_reconnect()
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщений: {e}")
            self.is_connected = False
            await self.schedule_reconnect()
    
    async def process_message(self, message: str):
        """Обработка входящего сообщения"""
        try:
            data = json.loads(message)
            logger.info(f"Получено сообщение от WebSocket Bridge: {data.get('requestId', 'no-id')}")
            
            request_id = data.get('requestId')
            if request_id and request_id in self.pending_requests:
                # Находим соответствующий запрос и отправляем ответ
                future = self.pending_requests.pop(request_id)
                if data.get('error'):
                    future.set_exception(Exception(data['error']))
                else:
                    future.set_result(data)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def schedule_reconnect(self):
        """Планирование переподключения"""
        if self.reconnect_attempts < self.config.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Переподключение через {self.config.reconnect_interval}с (попытка {self.reconnect_attempts})")
            await asyncio.sleep(self.config.reconnect_interval)
            await self.connect()
        else:
            logger.error("Достигнуто максимальное количество попыток переподключения")
    
    async def send_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка запроса через WebSocket Bridge"""
        if not self.is_connected or not self.websocket:
            raise Exception("WebSocket не подключен")
        
        self.request_id += 1
        request_id = self.request_id
        
        # Создаем future для ожидания ответа
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # Формируем запрос
        request = {
            **request_data,
            'requestId': request_id,
            'timestamp': int(time.time() * 1000)
        }
        
        try:
            logger.info(f"Отправка запроса в WebSocket Bridge: {request_id}")
            await self.websocket.send(json.dumps(request))
            
            # Ждем ответа с таймаутом
            response = await asyncio.wait_for(future, timeout=self.config.connection_timeout)
            logger.info(f"Получен ответ от WebSocket Bridge: {request_id}")
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise Exception("Таймаут ожидания ответа от WebSocket Bridge")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise e
    
    async def flush_message_queue(self):
        """Отправка накопленных сообщений"""
        if self.message_queue:
            logger.info(f"Отправка {len(self.message_queue)} накопленных сообщений")
            for message in self.message_queue:
                await self.websocket.send(json.dumps(message))
            self.message_queue.clear()
    
    def is_ready(self) -> bool:
        """Проверка готовности WebSocket соединения"""
        return self.is_connected and self.websocket and self.websocket.open
    
    async def close(self):
        """Закрытие WebSocket соединения"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False


class WebSocketProxyServer:
    """HTTP сервер для проксирования запросов через WebSocket Bridge"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, ws_url: str = "ws://localhost:8765"):
        self.host = host
        self.port = port
        self.ws_config = WebSocketConnection(url=ws_url)
        self.ws_client = WebSocketBridgeClient(self.ws_config)
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
    def setup_routes(self):
        """Настройка маршрутов"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/stats', self.stats_endpoint)
        self.app.router.add_post('/v1/chat/completions', self.chat_completions)
        self.app.router.add_post('/v1/*', self.proxy_other_endpoints)
        
    def setup_cors(self):
        """Настройка CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Применяем CORS ко всем маршрутам
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'websocket_connected': self.ws_client.is_ready(),
            'timestamp': datetime.now().isoformat()
        })
    
    async def stats_endpoint(self, request: web.Request) -> web.Response:
        """Статистика endpoint"""
        return web.json_response({
            'websocket_connected': self.ws_client.is_ready(),
            'pending_requests': len(self.ws_client.pending_requests),
            'queue_size': len(self.ws_client.message_queue),
            'reconnect_attempts': self.ws_client.reconnect_attempts
        })
    
    async def chat_completions(self, request: web.Request) -> web.Response:
        """OpenAI Chat Completions endpoint"""
        try:
            # Получаем данные запроса
            request_data = await request.json()
            logger.info(f"Получен OpenAI API запрос: {request.method} {request.path}")
            logger.info(f"Заголовки: {dict(request.headers)}")
            logger.info(f"Тело запроса: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
            
            # Проверяем готовность WebSocket
            if not self.ws_client.is_ready():
                logger.error("WebSocket не готов")
                return web.json_response({
                    'error': {
                        'message': 'WebSocket Bridge не подключен',
                        'type': 'connection_error',
                        'code': 'websocket_unavailable'
                    }
                }, status=503)
            
            # Проверяем, это streaming запрос
            is_streaming = request_data.get('stream', False)
            accept_header = request.headers.get('Accept', '')
            
            if is_streaming or 'text/event-stream' in accept_header:
                return await self.handle_streaming_request(request_data)
            else:
                return await self.handle_regular_request(request_data)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке chat completions: {e}")
            return web.json_response({
                'error': {
                    'message': str(e),
                    'type': 'internal_error',
                    'code': 'internal_error'
                }
            }, status=500)
    
    async def handle_regular_request(self, request_data: Dict[str, Any]) -> web.Response:
        """Обработка обычного запроса"""
        try:
            # Отправляем запрос через WebSocket Bridge
            response = await self.ws_client.send_request(request_data)
            
            # Формируем ответ в формате OpenAI API
            openai_response = {
                "id": response.get('id', f"chatcmpl-{int(time.time())}"),
                "object": "chat.completion",
                "created": response.get('created', int(time.time())),
                "model": response.get('model', request_data.get('model', 'gpt-4')),
                "choices": response.get('choices', [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.get('choices', [{}])[0].get('message', {}).get('content', 'Ответ получен через WebSocket Bridge')
                    },
                    "finish_reason": "stop"
                }]),
                "usage": response.get('usage', {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                })
            }
            
            logger.info("Ответ успешно сформирован")
            return web.json_response(openai_response)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке обычного запроса: {e}")
            return web.json_response({
                'error': {
                    'message': str(e),
                    'type': 'internal_error',
                    'code': 'internal_error'
                }
            }, status=500)
    
    async def handle_streaming_request(self, request_data: Dict[str, Any]) -> web.Response:
        """Обработка streaming запроса"""
        try:
            # Для streaming эмулируем потоковый ответ
            response = await self.ws_client.send_request(request_data)
            
            # Получаем контент из ответа
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            words = content.split()
            
            # Создаем streaming ответ
            stream_response = web.StreamResponse()
            stream_response.headers['Content-Type'] = 'text/event-stream'
            stream_response.headers['Cache-Control'] = 'no-cache'
            stream_response.headers['Connection'] = 'keep-alive'
            stream_response.headers['Access-Control-Allow-Origin'] = '*'
            
            await stream_response.prepare(web.Request(web.Message, web.Transport, web.Protocol))
            
            # Отправляем ответ по частям
            for i, word in enumerate(words):
                chunk = {
                    "id": response.get('id', f"chatcmpl-{int(time.time())}"),
                    "object": "chat.completion.chunk",
                    "created": response.get('created', int(time.time())),
                    "model": response.get('model', request_data.get('model', 'gpt-4')),
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": (word + " ") if i < len(words) - 1 else word
                        },
                        "finish_reason": None
                    }]
                }
                
                await stream_response.write(f"data: {json.dumps(chunk)}\n\n".encode())
                await asyncio.sleep(0.05)  # Небольшая задержка для эмуляции потока
            
            # Финальный chunk
            final_chunk = {
                "id": response.get('id', f"chatcmpl-{int(time.time())}"),
                "object": "chat.completion.chunk",
                "created": response.get('created', int(time.time())),
                "model": response.get('model', request_data.get('model', 'gpt-4')),
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            
            await stream_response.write(f"data: {json.dumps(final_chunk)}\n\n".encode())
            await stream_response.write(b"data: [DONE]\n\n")
            
            return stream_response
            
        except Exception as e:
            logger.error(f"Ошибка при обработке streaming запроса: {e}")
            return web.json_response({
                'error': {
                    'message': str(e),
                    'type': 'internal_error',
                    'code': 'internal_error'
                }
            }, status=500)
    
    async def proxy_other_endpoints(self, request: web.Request) -> web.Response:
        """Проксирование других OpenAI endpoints"""
        # Для других endpoints возвращаем заглушку
        return web.json_response({
            "object": "list",
            "data": []
        })
    
    async def start(self):
        """Запуск сервера"""
        # Подключаемся к WebSocket Bridge
        asyncio.create_task(self.ws_client.connect())
        
        # Даем время на подключение
        await asyncio.sleep(2)
        
        logger.info(f"Запуск Python WebSocket Proxy на {self.host}:{self.port}")
        logger.info(f"WebSocket Bridge URL: {self.ws_config.url}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"✅ Сервер запущен на http://{self.host}:{self.port}")
        logger.info(f"Health check: http://{self.host}:{self.port}/health")
        logger.info(f"OpenAI API: http://{self.host}:{self.port}/v1/chat/completions")
        
        # Работаем бесконечно
        await asyncio.Event().wait()


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Python WebSocket Proxy Client')
    parser.add_argument('--host', default='0.0.0.0', help='Хост для прослушивания')
    parser.add_argument('--port', type=int, default=8000, help='Порт для прослушивания')
    parser.add_argument('--ws-url', default='ws://localhost:8765', help='URL WebSocket Bridge')
    
    args = parser.parse_args()
    
    # Создаем и запускаем сервер
    server = WebSocketProxyServer(host=args.host, port=args.port, ws_url=args.ws_url)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Остановка сервера...")
        await server.ws_client.close()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await server.ws_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")