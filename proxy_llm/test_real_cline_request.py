#!/usr/bin/env python3
"""
Скрипт для отправки реального запроса от Cline к debug эндпоинту
для анализа структуры запроса и выявления неизвестных полей
"""

import requests
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_cline_request():
    """Отправляет запрос, имитирующий реальный запрос от Cline"""
    
    # URL debug эндпоинта
    url = "http://localhost:10014/debug/cline"
    
    # Заголовки, которые могут отправляться Cline
    headers = {
        "User-Agent": "Cline/1.0",
        "Content-Type": "application/json",
        "Authorization": "Bearer cline_api_key_123",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    # Тело запроса с максимально полной структурой
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": "Hello! How are you today?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": True,
        "stream_options": {
            "include_usage": True
        },
        "reasoning_effort": "medium",
        
        # Потенциальные дополнительные поля, которые может отправлять Cline
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
        
        # Специфичные поля, которые могут быть в Cline
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
        logger.info("Sending comprehensive Cline request to debug endpoint...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("=== DEBUG ANALYSIS ===")
            
            # Анализируем body
            body = data.get("body", {})
            logger.info(f"Parsed body keys: {list(body.keys())}")
            
            # Ищем неизвестные поля
            known_fields = {
                'model', 'messages', 'temperature', 'max_tokens', 'stream', 
                'reasoning_effort', 'stream_options', 'top_p', 'presence_penalty', 
                'frequency_penalty', 'logit_bias', 'user', 'suffix', 'echo', 
                'best_of', 'logprobs', 'n', 'stop'
            }
            
            unknown_fields = set(body.keys()) - known_fields
            if unknown_fields:
                logger.warning(f"⚠️  Unknown fields detected: {unknown_fields}")
                for field in unknown_fields:
                    logger.warning(f"   {field}: {body.get(field)}")
            else:
                logger.info("✅ No unknown fields detected")
            
            # Анализируем messages
            messages = body.get("messages", [])
            logger.info(f"Messages count: {len(messages)}")
            for i, msg in enumerate(messages):
                logger.info(f"Message {i}: role={msg.get('role')}, content_type={type(msg.get('content'))}")
                msg_keys = set(msg.keys())
                known_msg_keys = {'role', 'content', 'name'}
                unknown_msg_keys = msg_keys - known_msg_keys
                if unknown_msg_keys:
                    logger.warning(f"   Unknown message fields: {unknown_msg_keys}")
            
            # Анализируем raw body
            raw_body = data.get("raw_body", "")
            logger.info(f"Raw body length: {len(raw_body)}")
            logger.info(f"Raw body preview: {raw_body[:200]}...")
            
        else:
            logger.error(f"Request failed with status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending request: {e}")

def test_minimal_cline_request():
    """Отправляет минимальный запрос для проверки базовой функциональности"""
    
    url = "http://localhost:10014/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123"
    }
    
    payload = {
        "model": "test",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": False
    }
    
    try:
        logger.info("Sending minimal test request to main endpoint...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        logger.info(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            logger.info("✅ Minimal request successful!")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    print("=== Testing Real Cline Request Format ===")
    test_real_cline_request()
    
    print("\n=== Testing Minimal Request ===")
    test_minimal_cline_request()