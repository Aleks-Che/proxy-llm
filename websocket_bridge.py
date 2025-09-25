#!/usr/bin/env python3
"""
WebSocket Bridge для создания постоянного соединения между roocode и proxy-llm
Решает проблему сетевых ограничений и разрывов соединения
"""

import asyncio
import websockets
import json
import logging
import httpx
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    """Информация о клиентском соединении"""
    websocket: websockets.WebSocketServerProtocol
    client_id: str
    connected_at: datetime
    last_activity: datetime
    message_count: int = 0


class WebSocketBridge:
    """WebSocket мост для постоянного соединения с roocode"""
    
    def __init__(self, local_proxy_url: str = "http://localhost:8000"):
        self.local_proxy = local_proxy_url
        self.clients: Dict[str, ClientConnection] = {}
        self.message_queue: Dict[str, list] = {}
        self.reconnect_interval = 5  # секунды
        self.max_reconnect_attempts = 10
        self.connection_timeout = 30  # секунды
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol) -> str:
        """Регистрация нового клиента"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        self.clients[client_id] = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.message_queue[client_id] = []
        logger.info(f"Клиент зарегистрирован: {client_id}")
        return client_id
    
    async def unregister_client(self, client_id: str):
        """Отключение клиента"""
        if client_id in self.clients:
            logger.info(f"Клиент отключен: {client_id}")
            del self.clients[client_id]
            del self.message_queue[client_id]
    
    async def forward_to_proxy(self, client_id: str, request_data: dict) -> dict:
        """Перенаправление запроса в локальный прокси"""
        try:
            client = self.clients[client_id]
            client.last_activity = datetime.now()
            client.message_count += 1
            
            logger.info(f"Перенаправление запроса от {client_id}")
            
            # Определяем streaming режим
            is_streaming = request_data.get('stream', False)
            
            async with httpx.AsyncClient(timeout=60.0) as client_http:
                if is_streaming:
                    # Для streaming ответов используем streaming
                    async with client_http.stream(
                        'POST',
                        f"{self.local_proxy}/v1/chat/completions",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        # Собираем streaming ответ
                        accumulated_content = ""
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                data = line[6:]  # Убираем 'data: '
                                if data.strip() == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            accumulated_content += delta['content']
                                except json.JSONDecodeError:
                                    continue
                        
                        # Возвращаем полный ответ
                        return {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": request_data.get('model', 'unknown'),
                            "choices": [{
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": accumulated_content
                                },
                                "finish_reason": "stop"
                            }],
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": len(accumulated_content.split()),
                                "total_tokens": len(accumulated_content.split())
                            }
                        }
                else:
                    # Обычный запрос
                    response = await client_http.post(
                        f"{self.local_proxy}/v1/chat/completions",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Ошибка при перенаправлении запроса: {e}")
            return {
                "error": str(e),
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request_data.get('model', 'unknown'),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Ошибка прокси: {str(e)}"
                    },
                    "finish_reason": "stop"
                }]
            }
    
    async def handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Обработка сообщения от клиента"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        if client_id not in self.clients:
            logger.warning(f"Сообщение от незарегистрированного клиента: {client_id}")
            return
        
        try:
            # Парсим JSON запрос
            request_data = json.loads(message)
            logger.info(f"Получен запрос от {client_id}: {request_data.get('model', 'unknown')}")
            
            # Перенаправляем в локальный прокси
            response = await self.forward_to_proxy(client_id, request_data)
            
            # Отправляем ответ обратно
            await websocket.send(json.dumps(response))
            logger.info(f"Ответ отправлен клиенту {client_id}")
            
        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON format"}
            await websocket.send(json.dumps(error_response))
            logger.error(f"Неверный формат JSON от клиента {client_id}")
            
        except Exception as e:
            error_response = {"error": f"Server error: {str(e)}"}
            await websocket.send(json.dumps(error_response))
            logger.error(f"Ошибка обработки сообщения от {client_id}: {e}")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str = "/"):
        """Обработка WebSocket соединения с клиентом"""
        client_id = await self.register_client(websocket)
        
        try:
            logger.info(f"Новое соединение от {client_id}")
            
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Соединение закрыто клиентом: {client_id}")
        except Exception as e:
            logger.error(f"Ошибка в соединении с {client_id}: {e}")
        finally:
            await self.unregister_client(client_id)
    
    async def health_check(self):
        """Периодическая проверка здоровья сервиса"""
        while True:
            try:
                # Проверяем доступность локального прокси
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.local_proxy}/health", timeout=5.0)
                    if response.status_code != 200:
                        logger.warning(f"Локальный прокси не отвечает: {response.status_code}")
                    else:
                        logger.info("Локальный прокси работает нормально")
                        
            except Exception as e:
                logger.error(f"Ошибка проверки здоровья: {e}")
            
            await asyncio.sleep(30)  # Проверка каждые 30 секунд
    
    async def start_server(self, host: str = '0.0.0.0', port: int = 8765):
        """Запуск WebSocket сервера"""
        logger.info(f"Запуск WebSocket моста на {host}:{port}")
        logger.info(f"Проксируем запросы к: {self.local_proxy}")
        
        # Запускаем health check в фоне
        health_task = asyncio.create_task(self.health_check())
        
        try:
            async with websockets.serve(self.handle_client, host, port):
                logger.info("WebSocket сервер запущен")
                await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Остановка сервера...")
        finally:
            health_task.cancel()
            logger.info("Сервер остановлен")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket Bridge для proxy-llm')
    parser.add_argument('--host', default='0.0.0.0', help='Хост для прослушивания')
    parser.add_argument('--port', type=int, default=8765, help='Порт для прослушивания')
    parser.add_argument('--proxy-url', default='http://localhost:10002', help='URL локального прокси')
    
    args = parser.parse_args()
    
    bridge = WebSocketBridge(local_proxy_url=args.proxy_url)
    
    try:
        asyncio.run(bridge.start_server(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")


if __name__ == "__main__":
    main()