import asyncio
import json
from providers.deepseek import DeepSeekProvider

async def debug_deepseek_chunks_detailed():
    """Детальная диагностика структуры чанков от DeepSeek"""
    provider = DeepSeekProvider()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
    
    print("=== Детальная диагностика чанков от DeepSeek ===")
    print(f"Messages: {messages}")
    
    try:
        response = await provider.chat_completion(messages, stream=True, max_tokens=20)
        
        chunk_count = 0
        async for chunk in response:
            chunk_count += 1
            print(f"\n--- Чанк {chunk_count} ---")
            
            # Анализируем структуру чанка
            print(f"Тип чанка: {type(chunk)}")
            print(f"Атрибуты чанка: {[attr for attr in dir(chunk) if not attr.startswith('_')]}")
            
            # Проверяем различные методы доступа
            if hasattr(chunk, 'model_dump'):
                chunk_dict = chunk.model_dump()
                print("✓ Используем model_dump()")
            elif hasattr(chunk, 'dict'):
                chunk_dict = chunk.dict()
                print("✓ Используем dict()")
            elif hasattr(chunk, 'to_dict'):
                chunk_dict = chunk.to_dict()
                print("✓ Используем to_dict()")
            else:
                chunk_dict = {}
                print("✗ Нет стандартных методов сериализации")
            
            print(f"Содержимое чанка: {json.dumps(chunk_dict, indent=2, ensure_ascii=False)}")
            
            # Проверяем наличие usage данных
            if 'usage' in chunk_dict:
                usage = chunk_dict['usage']
                print(f"✓ Usage данные найдены: {usage}")
                if 'completion_tokens' in usage:
                    print(f"  completion_tokens: {usage['completion_tokens']}")
            else:
                print("✗ Usage данные отсутствуют")
            
            # Проверяем наличие content
            content = None
            if hasattr(chunk, 'content'):
                content = getattr(chunk, 'content')
                print(f"✓ Content из атрибута: '{content}'")
            elif 'choices' in chunk_dict and chunk_dict['choices']:
                choice = chunk_dict['choices'][0]
                if 'delta' in choice and 'content' in choice['delta']:
                    content = choice['delta']['content']
                    print(f"✓ Content из delta: '{content}'")
            
            if not content:
                print("✗ Content не найден")
            
            if chunk_count >= 3:  # Ограничиваем для анализа
                print("\n... останавливаемся после 3 чанков для анализа")
                break
                
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_deepseek_chunks_detailed())