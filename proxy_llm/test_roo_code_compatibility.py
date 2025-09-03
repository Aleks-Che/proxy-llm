#!/usr/bin/env python3
"""
Тестирование совместимости с расширением Roo-Code
Roo-Code использует стандартный OpenAI Chat Completions API
"""

import requests
import json
import logging
import asyncio
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync_roo_code_request():
    """Тестирование синхронного запроса в формате Roo-Code"""

    url = "http://localhost:10002/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123",
        "User-Agent": "Roo-Code/1.0"
    }

    # Запрос в формате Roo-Code
    payload = {
        "model": "gpt-4",  # ID модели
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
        "max_tokens": 1000,
        "stream": False,
        "stream_options": {
            "include_usage": True
        },
        "temperature": 0.7
    }

    try:
        logger.info("Testing Roo-Code sync request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        logger.info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Roo-Code sync request successful!")

            # Проверяем формат ответа
            required_fields = ["id", "object", "created", "model", "choices", "usage"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"❌ Missing required field: {field}")
                    return False

            if data["object"] != "chat.completion":
                logger.error(f"❌ Wrong object type: {data['object']}")
                return False

            if not data["choices"] or "message" not in data["choices"][0]:
                logger.error("❌ Invalid choices format")
                return False

            if "content" not in data["choices"][0]["message"]:
                logger.error("❌ Missing content in message")
                return False

            # Проверяем usage
            usage = data["usage"]
            required_usage = ["prompt_tokens", "completion_tokens", "total_tokens"]
            for field in required_usage:
                if field not in usage:
                    logger.error(f"❌ Missing usage field: {field}")
                    return False

            logger.info(f"Response format: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            return True
        else:
            logger.error(f"❌ Request failed: {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def test_async_roo_code_streaming():
    """Тестирование стримингового запроса в формате Roo-Code"""

    url = "http://localhost:10002/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123",
        "User-Agent": "Roo-Code/1.0"
    }

    # Streaming запрос в формате Roo-Code
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Tell me a short story about a cat"
            }
        ],
        "max_tokens": 200,
        "stream": True,
        "stream_options": {
            "include_usage": True
        },
        "temperature": 0.7
    }

    try:
        logger.info("Testing Roo-Code streaming request...")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:

                if response.status != 200:
                    logger.error(f"❌ Streaming request failed: {await response.text()}")
                    return False

                logger.info("✅ Streaming connection established!")

                # Читаем SSE события
                content = ""
                usage_received = False

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            logger.info("✅ Streaming completed successfully")
                            break

                        try:
                            chunk = json.loads(data)

                            # Проверяем формат chunk
                            if 'choices' in chunk and chunk['choices']:
                                choice = chunk['choices'][0]

                                # Проверяем наличие delta
                                if 'delta' in choice:
                                    delta = choice['delta']
                                    if 'content' in delta and delta['content']:
                                        content += delta['content']
                                        print(delta['content'], end='', flush=True)

                                # Проверяем finish_reason
                                if 'finish_reason' in choice and choice['finish_reason']:
                                    logger.info(f"Finish reason: {choice['finish_reason']}")

                            # Проверяем usage в финальном chunk
                            if 'usage' in chunk:
                                usage = chunk['usage']
                                required_usage = ["prompt_tokens", "completion_tokens", "total_tokens"]
                                for field in required_usage:
                                    if field not in usage:
                                        logger.error(f"❌ Missing usage field in stream: {field}")
                                        return False
                                logger.info(f"Usage stats: {usage}")
                                usage_received = True

                            # Проверяем обязательные поля chunk
                            required_chunk_fields = ["id", "object", "created", "model", "choices"]
                            for field in required_chunk_fields:
                                if field not in chunk:
                                    logger.error(f"❌ Missing chunk field: {field}")
                                    return False

                            if chunk["object"] != "chat.completion.chunk":
                                logger.error(f"❌ Wrong chunk object type: {chunk['object']}")
                                return False

                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON chunk: {data}")

                print()  # Новая строка после streaming
                logger.info(f"Final content length: {len(content)} characters")

                if not usage_received:
                    logger.warning("⚠️ Usage statistics not received in stream")

                return True

    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        return False

def test_minimal_roo_code_compatibility():
    """Тестирование минимального запроса Roo-Code"""

    url = "http://localhost:10002/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123"
    }

    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ]
    }

    try:
        logger.info("Testing minimal Roo-Code compatibility...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Minimal Roo-Code compatibility test passed!")
            return True
        else:
            logger.error(f"❌ Minimal test failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Minimal test error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Roo-Code Compatibility ===")

    # Тест 1: Минимальная совместимость
    test1 = test_minimal_roo_code_compatibility()

    # Тест 2: Полный синхронный запрос
    test2 = test_sync_roo_code_request()

    # Тест 3: Streaming запрос
    print("\n=== Testing Streaming ===")
    test3 = asyncio.run(test_async_roo_code_streaming())

    # Итоги
    print("\n=== RESULTS ===")
    print(f"Minimal compatibility: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Full sync request: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Streaming request: {'✅ PASS' if test3 else '❌ FAIL'}")

    if test1 and test2 and test3:
        print("🎉 ALL TESTS PASSED! Server is fully compatible with Roo-Code!")
    else:
        print("⚠️  Some tests failed. Check logs for details.")