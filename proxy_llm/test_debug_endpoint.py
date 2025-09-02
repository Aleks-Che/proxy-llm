import requests
import json

def test_debug_endpoint():
    """Тестирование debug эндпоинта для анализа запросов от Cline"""
    url = "http://localhost:10014/debug/cline"
    
    # Тестовые данные, имитирующие возможные форматы от Cline
    test_cases = [
        {
            "name": "Standard Cline format",
            "data": {
                "model": "test",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Привет! Как дела?"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": True,
                "stream_options": {"include_usage": True},
                "reasoning_effort": "medium"
            }
        },
        {
            "name": "With additional fields",
            "data": {
                "model": "test",
                "messages": [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False,
                "some_unknown_field": "unknown_value",  # Неизвестное поле
                "another_field": 123
            }
        },
        {
            "name": "Complex content types",
            "data": {
                "model": "test",
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Hello"},
                            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                        ]
                    }
                ]
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test123",
        "User-Agent": "Cline/1.0"
    }
    
    for i, test_case in enumerate(test_cases):
        print(f"\n=== Test {i+1}: {test_case['name']} ===")
        try:
            response = requests.post(url, json=test_case["data"], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_debug_endpoint()