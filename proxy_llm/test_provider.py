#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы провайдеров напрямую
"""

import asyncio
import aiohttp
import json
import time
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_local_provider():
    """Тест локального провайдера"""
    print("=== Тестирование локального провайдера ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Проверяем доступность llama-server
            try:
                async with session.get("http://localhost:10003/health") as response:
                    health = await response.text()
                    print(f"✅ llama-server health: {health}")
            except Exception as e:
                print(f"❌ llama-server недоступен: {e}")
                return
            
            # Тестируем chat completions
            payload = {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Привет, как дела?"}
                ],
                "max_tokens": 50
            }
            
            print("Отправка запроса...")
            start_time = time.time()
            
            async with session.post(
                "http://localhost:10003/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed = time.time() - start_time
                print(f"Ответ получен за {elapsed:.2f} секунд")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Ответ:", data['choices'][0]['message']['content'][:100] + "...")
                else:
                    print(f"❌ Ошибка: {response.status} - {await response.text()}")
                    
    except asyncio.TimeoutError:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_proxy_server():
    """Тест прокси-сервера"""
    print("\n=== Тестирование прокси-сервера ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Привет, как дела?"}
                ],
                "max_tokens": 50
            }
            
            print("Отправка запроса в прокси...")
            start_time = time.time()
            
            async with session.post(
                "http://localhost:10002/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed = time.time() - start_time
                print(f"Ответ получен за {elapsed:.2f} секунд")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Ответ:", data['choices'][0]['message']['content'][:100] + "...")
                else:
                    print(f"❌ Ошибка: {response.status} - {await response.text()}")
                    
    except asyncio.TimeoutError:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_proxy_server())