#!/bin/bash
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
