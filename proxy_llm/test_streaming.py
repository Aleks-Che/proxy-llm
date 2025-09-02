import requests
import json
import time

def test_streaming():
    """Тестирование streaming запроса"""
    url = "http://localhost:10006/v1/chat/completions"
    
    # Тело запроса с включенным стримингом
    data = {
        "model": "test",
        "messages": [
            {
                "role": "user", 
                "content": "Расскажи мне о преимуществах искусственного интеллекта"
            }
        ],
        "stream": True,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123"
    }
    
    print("Testing streaming request...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, stream=True)
        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Streaming response received:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        content = line_str[6:]  # Убираем 'data: '
                        if content != '[DONE]':
                            try:
                                chunk = json.loads(content)
                                if 'choices' in chunk and chunk['choices']:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        print(delta['content'], end='', flush=True)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON: {content}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_streaming()