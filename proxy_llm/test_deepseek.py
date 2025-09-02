#!/usr/bin/env python3
"""
Тестовый скрипт для проверки DeepSeek провайдера
"""

import asyncio
import aiohttp
import json
import time
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_deepseek_direct():
    """Тест DeepSeek напрямую"""
    print("=== Тестирование DeepSeek напрямую ===")
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key or api_key == 'sk-ваш-ключ-здесь':
        print("❌ Не задан DEEPSEEK_API_KEY в .env")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "Привет, как дела?"}
                ],
                "max_tokens": 50
            }
            
            print("Отправка запроса в DeepSeek...")
            start_time = time.time()
            
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed = time.time() - start_time
                print(f"Ответ получен за {elapsed:.2f} секунд")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Ответ:", data['choices'][0]['message']['content'][:100] + "...")
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка: {response.status} - {error_text}")
                    
    except asyncio.TimeoutError:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_deepseek_via_proxy():
    """Тест DeepSeek через прокси"""
    print("\n=== Тестирование DeepSeek через прокси ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Сначала переключаем провайдера на deepseek
            async with session.post(
                "http://localhost:10002/switch-provider/deepseek",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as switch_response:
                if switch_response.status != 200:
                    print("❌ Не удалось переключить провайдера")
                    return
                
            payload = {
                "model": "deepseek-chat",
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
                    error_text = await response.text()
                    print(f"❌ Ошибка: {response.status} - {error_text}")
                    
    except asyncio.TimeoutError:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepseek_direct())
    asyncio.run(test_deepseek_via_proxy())