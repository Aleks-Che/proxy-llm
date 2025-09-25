#!/usr/bin/env python3
"""
Скрипт установки и настройки WebSocket прокси для proxy-llm
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def install_dependencies():
    """Установка необходимых зависимостей"""
    print("Установка зависимостей...")
    
    dependencies = [
        "websockets>=11.0",
        "httpx>=0.24.0",
        "aiohttp>=3.8.0"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ Установлено: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка установки {dep}: {e}")
            return False
    
    return True

def create_systemd_service():
    """Создание systemd сервиса для автозапуска"""
    service_content = """[Unit]
Description=WebSocket Bridge for proxy-llm
After=network.target proxy-llm.service

[Service]
Type=simple
User=%USER%
WorkingDirectory=%WORKING_DIR%
ExecStart=%PYTHON% %SCRIPT_PATH%
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    
    # Заменяем переменные
    service_content = service_content.replace('%USER%', os.getenv('USER', 'root'))
    service_content = service_content.replace('%WORKING_DIR%', os.getcwd())
    service_content = service_content.replace('%PYTHON%', sys.executable)
    service_content = service_content.replace('%SCRIPT_PATH%', os.path.join(os.getcwd(), 'websocket_bridge.py'))
    
    service_path = Path.home() / '.config' / 'systemd' / 'user' / 'websocket-bridge.service'
    
    try:
        service_path.parent.mkdir(parents=True, exist_ok=True)
        service_path.write_text(service_content)
        print(f"✓ Создан systemd сервис: {service_path}")
        
        # Активируем сервис
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', 'websocket-bridge.service'], check=True)
        print("✓ Сервис активирован для автозапуска")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка создания сервиса: {e}")
        return False

def create_config_file():
    """Создание конфигурационного файла"""
    config = {
        "websocket_bridge": {
            "host": "0.0.0.0",
            "port": 8765,
            "local_proxy_url": "http://localhost:10002",
            "reconnect_interval": 5,
            "max_reconnect_attempts": 10,
            "connection_timeout": 30,
            "heartbeat_interval": 15
        },
        "client": {
            "ws_url": "ws://localhost:8765",
            "reconnect_interval": 5000,
            "max_reconnect_attempts": 10,
            "connection_timeout": 30000,
            "heartbeat_interval": 15000
        },
        "network": {
            "keepalive_interval": 30,
            "retry_delay": 10,
            "max_retries": 5
        }
    }
    
    config_path = Path('websocket_config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Создан конфигурационный файл: {config_path}")
        return True
    except Exception as e:
        print(f"✗ Ошибка создания конфигурационного файла: {e}")
        return False

def create_startup_script():
    """Создание скрипта запуска"""
    startup_script = """#!/bin/bash
# WebSocket Bridge Startup Script

echo "Запуск WebSocket Bridge для proxy-llm..."

# Проверяем, запущен ли proxy-llm
if ! curl -s http://localhost:10002/health > /dev/null; then
    echo "⚠️  proxy-llm не запущен. Пожалуйста, запустите его сначала."
    echo "   python server.py"
    exit 1
fi

echo "✓ proxy-llm работает"

# Запускаем WebSocket Bridge
python3 websocket_bridge.py "$@"

# Если скрипт завершился с ошибкой, показываем сообщение
if [ $? -ne 0 ]; then
    echo "✗ Ошибка запуска WebSocket Bridge"
    echo "Проверьте логи выше для деталей"
    exit 1
fi
"""
    
    script_path = Path('start_websocket_bridge.sh')
    
    try:
        script_path.write_text(startup_script, encoding='utf-8')
        script_path.chmod(0o755)  # Делаем исполняемым
        print(f"✓ Создан скрипт запуска: {script_path}")
        return True
    except Exception as e:
        print(f"✗ Ошибка создания скрипта запуска: {e}")
        return False

def create_test_script():
    """Создание тестового скрипта"""
    test_script = """#!/usr/bin/env python3
\"\"\"
Тестовый скрипт для проверки WebSocket Bridge
\"\"\"

import asyncio
import websockets
import json
import sys

async def test_connection():
    \"\"\"Тестирование соединения с WebSocket Bridge\"\"\"
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f\"✓ Подключено к {uri}\")
            
            # Тестовый запрос
            test_request = {
                \"model\": \"gpt-4\",
                \"messages\": [
                    {\"role\": \"user\", \"content\": \"Hello, this is a test message. Please respond with 'Test successful'.\"}
                ],
                \"max_tokens\": 50,
                \"temperature\": 0.7
            }
            
            print(\"Отправка тестового запроса...\") 
            await websocket.send(json.dumps(test_request))
            
            # Ждем ответ
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            response_data = json.loads(response)
            
            if \"error\" in response_data:
                print(f\"✗ Ошибка от сервера: {response_data['error']}\")
                return False
            else:
                print(\"✓ Ответ получен успешно\")
                print(f\"Модель: {response_data.get('model', 'unknown')}\")
                content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f\"Содержимое: {content[:100]}...\" if len(content) > 100 else f\"Содержимое: {content}\")
                return True
                
    except asyncio.TimeoutError:
        print(\"✗ Таймаут ожидания ответа\")
        return False
    except Exception as e:
        print(f\"✗ Ошибка тестирования: {e}\")
        return False

async def test_streaming():
    \"\"\"Тестирование streaming режима\"\"\"
    uri = \"ws://localhost:8765\"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f\"✓ Подключено к {uri} для streaming теста\")
            
            # Тестовый streaming запрос
            test_request = {
                \"model\": \"gpt-4\",
                \"messages\": [
                    {\"role\": \"user\", \"content\": \"Count from 1 to 5 slowly\"}
                ],
                \"stream\": True,
                \"max_tokens\": 50
            }
            
            print(\"Отправка streaming запроса...\") 
            await websocket.send(json.dumps(test_request))
            
            # Жем ответ
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            response_data = json.loads(response)
            
            if \"error\" in response_data:
                print(f\"✗ Ошибка streaming: {response_data['error']}\")
                return False
            else:
                print(\"✓ Streaming ответ получен успешно\")
                content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f\"Содержимое: {content}\")
                return True
                
    except Exception as e:
        print(f\"✗ Ошибка streaming теста: {e}\")
        return False

async def main():
    \"\"\"Главная функция тестирования\"\"\"
    print(\"Тестирование WebSocket Bridge\")
    print(\"=\" * 40)
    
    # Проверяем, запущен ли WebSocket Bridge
    try:
        async with websockets.connect(\"ws://localhost:8765\") as _:
            pass
    except:
        print(\"✗ WebSocket Bridge не запущен\")
        print(\"  Запустите: python websocket_bridge.py\")
        return
    
    print(\"✓ WebSocket Bridge запущен\")
    print()
    
    # Тест обычного запроса
    print(\"1. Тест обычного запроса:\")
    success1 = await test_connection()
    print()
    
    # Тест streaming запроса
    print(\"2. Тест streaming запроса:\")
    success2 = await test_streaming()
    print()
    
    # Итоги
    print(\"Результаты тестирования:\")
    print(\"=\" * 40)
    print(f\"Обычный запрос: {'✓ УСПЕШНО' if success1 else '✗ ОШИБКА'}\")
    print(f\"Streaming запрос: {'✓ УСПЕШНО' if success2 else '✗ ОШИБКА'}\")
    
    if success1 and success2:
        print(\"\\n🎉 Все тесты пройдены успешно!\")
        return 0
    else:
        print(\"\\n❌ Некоторые тесты не пройдены\")
        return 1

if __name__ == \"__main__\":
    result = asyncio.run(main())
    sys.exit(result)
"""
    
    script_path = Path('test_websocket_bridge.py')
    
    try:
        script_path.write_text(test_script, encoding='utf-8')
        script_path.chmod(0o755)
        print(f"✓ Создан тестовый скрипт: {script_path}")
        return True
    except Exception as e:
        print(f"✗ Ошибка создания тестового скрипта: {e}")
        return False

def main():
    """Главная функция установки"""
    print("Установка WebSocket Bridge для proxy-llm")
    print("=" * 50)
    
    success = True
    
    # Шаг 1: Установка зависимостей
    print("\\n1. Установка зависимостей:")
    success &= install_dependencies()
    
    # Шаг 2: Создание конфигурационного файла
    print("\\n2. Создание конфигурации:")
    success &= create_config_file()
    
    # Шаг 3: Создание скриптов
    print("\\n3. Создание скриптов:")
    success &= create_startup_script()
    success &= create_test_script()
    
    # Шаг 4: Создание systemd сервиса (опционально)
    print("\\n4. Создание systemd сервиса (опционально):")
    response = input("Создать systemd сервис для автозапуска? [y/N]: ").lower()
    if response == 'y':
        success &= create_systemd_service()
    
    print("\\n" + "=" * 50)
    if success:
        print("✅ Установка завершена успешно!")
        print("\\nДальнейшие шаги:")
        print("1. Запустите proxy-llm: python server.py")
        print("2. Запустите WebSocket Bridge: ./start_websocket_bridge.sh")
        print("3. Протестируйте: python test_websocket_bridge.py")
        print("\\nДля использования в roocode/cline:")
        print("- Укажите URL: ws://localhost:8765")
        print("- Используйте клиентский код из websocket_client.js")
    else:
        print("❌ Установка завершена с ошибками")
        print("Проверьте сообщения выше и исправьте проблемы")

if __name__ == "__main__":
    main()