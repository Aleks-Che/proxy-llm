import requests
import json
import time

def test_cline_format():
    """Тестирование запроса в формате Cline"""
    url = "http://localhost:10002/v1/chat/completions"
    
    # Тело запроса в точном формате Cline
    data = {
        "model": "test",
        "messages": [
            {
                "role": "user", 
                "content": "Привет! Как дела?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": True,
        "stream_options": {"include_usage": True},
        "reasoning_effort": "medium"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123",
        "User-Agent": "Fs/JS 4.83.0",
        "X-Stainless-Lang": "js",
        "X-Stainless-Package-Version": "4.83.0",
        "X-Stainless-OS": "Linux", 
        "X-Stainless-Arch": "x64",
        "X-Stainless-Runtime": "node",
        "X-Stainless-Runtime-Version": "v20.16.0"
    }
    
    print("Testing Cline format request...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
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
                                print(f"Chunk: {json.dumps(chunk, ensure_ascii=False)}")
                                
                                # Проверяем структуру ответа
                                if 'choices' in chunk and chunk['choices']:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        print(f"Content: {delta['content']}")
                                    
                                if 'usage' in chunk:
                                    print(f"Usage: {chunk['usage']}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"Invalid JSON: {content}, Error: {e}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_cline_format()