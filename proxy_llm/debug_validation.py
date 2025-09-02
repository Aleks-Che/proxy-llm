import requests
import json
import time

def debug_validation_error():
    """Диагностика ошибки валидации 422"""
    url = "http://localhost:10009/v1/chat/completions"
    
    # Пробуем разные варианты запросов
    test_cases = [
        {
            "name": "Real Cline format",
            "data": {
                "model": "test",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Привет! Как дела?"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": True,
                "stream_options": {"include_usage": True}
            }
        },
        {
            "name": "Simple format",
            "data": {
                "model": "test",
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "stream": False
            }
        },
        {
            "name": "Minimal format", 
            "data": {
                "model": "test",
                "messages": [
                    {"role": "user", "content": "test"}
                ]
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123"
    }
    
    for i, test_case in enumerate(test_cases):
        print(f"\n=== Test {i+1}: {test_case['name']} ===")
        print(f"Request: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, json=test_case['data'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 422:
                print("🔴 422 Validation Error!")
                try:
                    error_data = response.json()
                    print(f"Error details: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                except:
                    print(f"Raw error: {response.text}")
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_validation_error()