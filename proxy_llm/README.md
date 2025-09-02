# LLM Proxy

Python приложение для проксирования запросов к LLM API (DeepSeek, Moonshot) с OpenAI-compatible интерфейсом.

## Установка

1. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

2. Создайте файл `.env` на основе `.env.example` и заполните API ключи:

   ```bash
   cp .env.example .env
   ```

   Отредактируйте `.env`:

   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   MOONSHOT_API_KEY=your_moonshot_api_key
   DEEPSEEK_MODEL=deepseek-chat
   MOONSHOT_MODEL=kimi-k2-0711-preview
   ```

## Запуск

Сначала проверьте, свободен ли порт 8000:

```bash
python check_port.py
```

Если порт занят другим процессом, завершите его или измените порт в `.env` файле.

### GUI режим (рекомендуется)

Запустите GUI для управления сервером:

```bash
python main.py
```

### Режим сервера

Запустите только сервер в фоне:

```bash
python run_server.py
```

Или запустите сервер напрямую:

```bash
python server.py
```

**Важно:** Сервер теперь слушает только localhost (127.0.0.1), что предотвращает автоматические запросы от других приложений.

## Использование

1. В GUI нажмите "Запустить сервер"
2. Выберите провайдера (DeepSeek или Moonshot)
3. Отправляйте запросы на `http://localhost:8000/v1/chat/completions` в формате OpenAI

**Примечание:** Порт сервера можно изменить в файле `.env` (по умолчанию 8000)

## Настройка расширений IDE

### VS Code + Cline

Если вы используете расширение Cline, убедитесь, что оно настроено правильно:

1. Откройте настройки Cline
2. Найдите настройку "OpenAI Base URL" или аналогичную
3. Установите значение: `http://localhost:8000/v1`
4. API Key можно оставить любой (прокси-сервер его игнорирует)
5. Сохраните настройки

**Важно:** API ключ и модель в настройках Cline НЕ влияют на работу прокси-сервера. Прокси использует свои собственные ключи и модели из файла `.env`.

### Другие расширения

Для других расширений, поддерживающих OpenAI-compatible API:

- **Base URL:** `http://localhost:8000` или `http://localhost:8000/v1`
- **API Key:** Любой непустой ключ (не используется прокси-сервером)

### Тестирование

Сначала проверьте, запущен ли сервер:

```bash
python check_server.py
```

Для тестирования API используйте тестовый клиент:

```bash
python test_client.py
```

Для тестирования v1 API (совместимость с OpenAI):

```bash
python test_v1.py
```

Для отладки различных форматов запросов:

```bash
python debug_request.py
```

Для тестирования формата запросов от Cline:

```bash
python test_cline_format.py
```

Для быстрого тестирования сервера:

```bash
python quick_test.py
```

Для проверки доступных маршрутов:

```bash
python check_routes.py
```

Для автоматического запуска сервера и тестирования:

```bash
python start_and_test.py
```

Пример запроса:

```python
import requests

response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

## Функции

- Проксирование OpenAI-compatible запросов
- Выбор между DeepSeek и Moonshot
- Отображение статистики (запросы, токены, стоимость)
- Логирование запросов в GUI
