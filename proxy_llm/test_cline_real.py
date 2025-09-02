import requests
import json
import time

def test_cline_real():
    """Тестирование реального формата запроса Cline (без reasoning_effort)"""
    url = "http://localhost:10013/v1/chat/completions"
    
    # Тело запроса в реальном формате Cline (без reasoning_effort)
    data = {
        "model": "test",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": "Привет! Как дела?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": True,
        "stream_options": {"include_usage": True}
        # reasoning_effort не включаем - Cline не отправляет его для обычных моделей
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123",
        "User-Agent": "OpenAI/NodeJS/1.0.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }
    
    print("Testing real Cline format request (without reasoning_effort)...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Streaming response received:")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        content = line_str[6:]  # Убираем 'data: '
                        if content == '[DONE]':
                            print("Received [DONE] signal")
                            break
                            
                        try:
                            chunk = json.loads(content)
                            chunk_count += 1
                            
                            if chunk_count <= 3:  # Показываем только первые 3 chunks для анализа
                                print(f"Chunk {chunk_count}: {json.dumps(chunk, ensure_ascii=False)}")
                            
                            # Проверяем структуру ответа
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta and delta['content']:
                                    print(f"Content: '{delta['content']}'")
                                    
                            if 'usage' in chunk:
                                usage = chunk['usage']
                                print(f"Usage: prompt_tokens={usage.get('prompt_tokens', 0)}, completion_tokens={usage.get('completion_tokens', 0)}")
                                
                        except json.JSONDecodeError as e:
                            print(f"Invalid JSON: {content}, Error: {e}")
                            break
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_cline_real()