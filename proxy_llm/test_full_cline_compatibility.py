#!/usr/bin/env python3
"""
Тестирование полной совместимости с реальными запросами от Cline
"""

import requests
import json
import logging
import asyncio
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync_cline_request():
    """Тестирование синхронного запроса с полными полями от Cline"""
    
    url = "http://localhost:10014/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123",
        "User-Agent": "Cline/1.0"
    }
    
    # Полный запрос с реальными полями от Cline
    payload = {
        "model": "test",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello! Can you help me with something?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False,
        "stream_options": {
            "include_usage": True
        },
        "reasoning_effort": "medium",
        "top_p": 0.9,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "logit_bias": {},
        "user": "user123",
        "n": 1,
        "stop": None,
        "best_of": 1,
        "logprobs": None,
        "echo": False,
        "suffix": None,
        "tools": [],
        "tool_choice": "auto",
        "response_format": {"type": "text"},
        "seed": 42,
        "max_completion_tokens": 1000,
        "truncation_strategy": {
            "type": "auto",
            "last_messages": 10
        },
        "reasoning": {
            "type": "structured",
            "format": "markdown"
        },
        "parallel_tool_calls": True,
        "store": True,
        "metadata": {
            "user_id": "12345",
            "session_id": "67890"
        }
    }
    
    try:
        logger.info("Testing full Cline compatibility (sync)...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Full Cline request successful!")
            logger.info(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            logger.error(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def test_async_cline_streaming():
    """Тестирование асинхронного streaming запроса"""
    
    url = "http://localhost:10014/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123",
        "User-Agent": "Cline/1.0"
    }
    
    # Streaming запрос
    payload = {
        "model": "test",
        "messages": [
            {
                "role": "user",
                "content": "Tell me a short story about a cat"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 200,
        "stream": True,
        "stream_options": {
            "include_usage": True
        },
        "reasoning_effort": "low"
    }
    
    try:
        logger.info("Testing Cline streaming compatibility...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                
                if response.status != 200:
                    logger.error(f"❌ Streaming request failed: {await response.text()}")
                    return False
                
                logger.info("✅ Streaming connection established!")
                
                # Читаем SSE события
                content = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            logger.info("✅ Streaming completed successfully")
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta and delta['content']:
                                    content += delta['content']
                                    print(delta['content'], end='', flush=True)
                                
                                # Логируем usage статистику если есть
                                if 'usage' in chunk:
                                    logger.info(f"Usage stats: {chunk['usage']}")
                                    
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON chunk: {data}")
                
                print()  # Новая строка после streaming
                logger.info(f"Final content length: {len(content)} characters")
                return True
                
    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        return False

def test_minimal_compatibility():
    """Тестирование минимального запроса для базовой проверки"""
    
    url = "http://localhost:10014/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123"
    }
    
    payload = {
        "model": "test",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ]
    }
    
    try:
        logger.info("Testing minimal compatibility...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Minimal compatibility test passed!")
            return True
        else:
            logger.error(f"❌ Minimal test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Minimal test error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Full Cline Compatibility ===")
    
    # Тест 1: Минимальная совместимость
    test1 = test_minimal_compatibility()
    
    # Тест 2: Полный синхронный запрос
    test2 = test_sync_cline_request()
    
    # Тест 3: Streaming запрос
    print("\n=== Testing Streaming ===")
    test3 = asyncio.run(test_async_cline_streaming())
    
    # Итоги
    print(f"\n=== RESULTS ===")
    print(f"Minimal compatibility: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Full sync request: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Streaming request: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if test1 and test2 and test3:
        print("🎉 ALL TESTS PASSED! Server is fully compatible with Cline!")
    else:
        print("⚠️  Some tests failed. Check logs for details.")