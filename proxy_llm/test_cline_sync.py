
#!/usr/bin/env python3
"""
Синхронный тестовый скрипт для имитации запросов от Cline
"""

import requests
import json

def test_cline_format():
    """Тест формата запроса от Cline"""
    print("=== Тестирование формата Cline ===")
    
    try:
        # Формат запроса, который может отправлять Cline
        payload = {
            "model": "gpt-oss-120b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Cline, a highly skilled software engineer..."
                },
                {
                    "role": "user", 
                    "content": "Напиши код для функции сложения двух чисел"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False,
            # Возможные дополнительные поля от Cline
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None
        }
        
        print("Отправка запроса в формате Cline...")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            "http://localhost:10002/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Ответ получен: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ!")
            print(f"Ответ: {data['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_minimal_cline_format():
    """Тест минимального формата запроса от Cline"""
    print("\n=== Тестирование минимального формата Cline ===")
    
    try:
        # Минимальный формат запроса
        payload = {
            "model": "gpt-oss-120b",
            "messages": [
                {
                    "role": "user", 
                    "content": "Привет"
                }
            ]
        }
        
        print("Отправка минимального запроса...")
        
        response = requests.post(
            "http://localhost:10002/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Ответ получен: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ!")
            print(f"Ответ: {data['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_cline_format()
    test_minimal_cline_format()
