#!/usr/bin/env python3
"""
Скрипт для тестирования кодировки и отправки запросов
"""

import requests
import json

def test_encoding():
    """Тест кодировки"""
    print("=== Тестирование кодировки ===")
    
    # Создаем запрос с кириллицей
    payload = {
        "model": "gpt-oss-120b",
        "messages": [
            {
                "role": "user", 
                "content": "Привет"
            }
        ]
    }
    
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:10002/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ!")
        else:
            print("❌ Ошибка")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_with_english():
    """Тест с английским текстом"""
    print("\n=== Тестирование с английским текстом ===")
    
    payload = {
        "model": "gpt-oss-120b",
        "messages": [
            {
                "role": "user", 
                "content": "Hello"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:10002/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_encoding()
    test_with_english()