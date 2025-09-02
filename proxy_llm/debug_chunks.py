import asyncio
import json
from providers.deepseek import DeepSeekProvider

async def debug_deepseek_chunks():
    """Диагностика структуры чанков от DeepSeek"""
    provider = DeepSeekProvider()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
    
    print("=== Testing DeepSeek provider chunks ===")
    print(f"Messages: {messages}")
    
    try:
        response = await provider.chat_completion(messages, stream=True, max_tokens=50)
        
        chunk_count = 0
        async for chunk in response:
            chunk_count += 1
            print(f"\n--- Chunk {chunk_count} ---")
            
            # Проверяем структуру чанка
            if hasattr(chunk, 'to_dict'):
                chunk_dict = chunk.to_dict()
                print(f"Chunk type: to_dict() available")
            elif hasattr(chunk, 'dict'):
                chunk_dict = chunk.dict()
                print(f"Chunk type: dict() available")
            else:
                chunk_dict = {}
                print(f"Chunk type: unknown - {type(chunk)}")
                print(f"Chunk attributes: {dir(chunk)}")
            
            # Выводим содержимое чанка
            print(f"Chunk content: {chunk_dict}")
            
            # Проверяем наличие usage данных
            if 'usage' in chunk_dict:
                print(f"Usage in chunk: {chunk_dict['usage']}")
            else:
                print("No usage data in chunk")
            
            # Проверяем наличие content
            content = getattr(chunk, 'content', None)
            if content:
                print(f"Content: '{content}'")
            else:
                # Проверяем структуру choices
                if 'choices' in chunk_dict and chunk_dict['choices']:
                    choice = chunk_dict['choices'][0]
                    if 'delta' in choice and 'content' in choice['delta']:
                        content = choice['delta']['content']
                        print(f"Content from delta: '{content}'")
            
            if chunk_count >= 5:  # Ограничиваем количество чанков для анализа
                break
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_deepseek_chunks())